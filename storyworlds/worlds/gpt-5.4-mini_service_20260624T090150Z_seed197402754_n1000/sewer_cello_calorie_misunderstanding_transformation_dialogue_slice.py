#!/usr/bin/env python3
"""
Storyworld: sewer / cello / calorie misunderstanding transformation dialogue slice.

A small slice-of-life world about a child and a caregiver who misread a calorie
count, move through a mild misunderstanding, and end with a quiet transformation
that changes how they spend the afternoon together.
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
class Person:
    name: str
    role: str
    mood: str = "calm"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class ObjectThing:
    name: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Mina"
    adult_name: str = "Jules"
    place: str = "the little kitchen"
    snack: str = "apple cake"
    instrument: str = "cello"
    misunderstanding: str = "calorie"
    transformation: str = "recipe"
    tone: str = "slice of life"


PEOPLE = {
    "Mina": {"role": "child"},
    "Jules": {"role": "adult"},
    "Noor": {"role": "child"},
    "Tessa": {"role": "adult"},
    "Leo": {"role": "child"},
    "Robin": {"role": "adult"},
}

PLACES = [
    "the little kitchen",
    "the back porch",
    "the sunny apartment",
    "the community room",
]

SNACKS = [
    "apple cake",
    "banana bread",
    "oat cookies",
    "pear muffins",
]

INSTRUMENTS = ["cello", "tiny cello", "practice cello"]

MISUNDERSTANDINGS = ["calorie", "calories", "calorie note"]

TRANSFORMATIONS = [
    "recipe card",
    "shopping list",
    "practice schedule",
    "lunch box label",
]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.people: dict[str, Person] = {
            params.child_name: Person(params.child_name, "child"),
            params.adult_name: Person(params.adult_name, "adult"),
        }
        self.objects: dict[str, ObjectThing] = {
            "cello": ObjectThing("cello", params.instrument),
            "snack": ObjectThing("snack", params.snack),
            "note": ObjectThing("note", params.misunderstanding),
        }
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with a cello, a calorie misunderstanding, and a gentle transformation.")
    ap.add_argument("--child-name", choices=sorted(PEOPLE.keys()))
    ap.add_argument("--adult-name", choices=sorted(PEOPLE.keys()))
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
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
    child_name = args.child_name or rng.choice(["Mina", "Noor", "Leo"])
    adult_name = args.adult_name or rng.choice([n for n in ["Jules", "Tessa", "Robin"] if n != child_name])
    if child_name == adult_name:
        raise StoryError("The child and adult must be different people.")

    return StoryParams(
        seed=None,
        child_name=child_name,
        adult_name=adult_name,
        place=args.place or rng.choice(PLACES),
        snack=args.snack or rng.choice(SNACKS),
        instrument=args.instrument or rng.choice(INSTRUMENTS),
        misunderstanding=args.misunderstanding or rng.choice(MISUNDERSTANDINGS),
        transformation=args.transformation or rng.choice(TRANSFORMATIONS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for snack in SNACKS:
        lines.append(asp.fact("snack", snack))
    for inst in INSTRUMENTS:
        lines.append(asp.fact("instrument", inst))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    for t in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", t))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(C, A, P, S, I, M, T) :- child(C), adult(A), place(P), snack(S), instrument(I), misunderstanding(M), transformation(T), C != A.
#show valid_story/7.
"""


def asp_program(show: str) -> str:
    return f"""
{asp_facts()}
child("Mina"). child("Noor"). child("Leo").
adult("Jules"). adult("Tessa"). adult("Robin").
{ASP_RULES}
{show}
"""


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/7."))
    atoms = asp.atoms(model, "valid_story")
    if atoms:
        print(f"OK: ASP produced {len(atoms)} generic story shapes.")
        return 0
    print("ASP verification failed.")
    return 1


def tell(params: StoryParams) -> World:
    world = World(params)
    child = world.people[params.child_name]
    adult = world.people[params.adult_name]
    cello = world.objects["cello"]
    snack = world.objects["snack"]
    note = world.objects["note"]

    child.meters["curiosity"] = 1
    child.memes["anticipation"] = 1
    adult.meters["care"] = 1
    snack.meters["sweetness"] = 1
    cello.meters["quiet_weight"] = 1

    world.say(
        f"{child.name} was spending the afternoon in {params.place}, "
        f"where the air felt ordinary and warm."
    )
    world.say(
        f"On the table sat {params.snack}, and beside it waited a {params.instrument} "
        f"with a soft, brown shine."
    )
    world.say(
        f"{child.name} loved the sound of the {params.instrument}, but "
        f"{adult.name} kept glancing at the {params.misunderstanding} note on the counter."
    )

    world.para()
    child.memes["wanting"] = 1
    adult.memes["worry"] = 1
    world.say(
        f"\"Can I have a slice before practice?\" {child.name} asked."
    )
    world.say(
        f"\"Maybe after we check the {params.misunderstanding} count,\" "
        f"{adult.name} said, pointing at the note."
    )
    world.say(
        f"{child.name} blinked. \"I thought the note meant I wasn't allowed to touch the cello,\" "
        f"{child.name} said."
    )
    world.say(
        f"{adult.name} laughed softly. \"No, sweetheart. I only meant the snack had more "
        f"{params.misunderstanding}s than I expected.\""
    )
    child.memes["misunderstood"] = 1
    adult.memes["relief"] = 1

    world.para()
    world.say(
        f"That made the room feel lighter."
    )
    world.say(
        f"{child.name} slid the note closer and read it again with {adult.name} looking over {child.name}'s shoulder."
    )
    world.say(
        f"Together they changed the {params.transformation} into a new {params.transformation} that said, "
        f"\"One small slice, then cello practice.\""
    )
    note.label = params.transformation
    note.meters["organized"] = 1
    child.memes["understanding"] = 1
    child.meters["calm"] = 1
    adult.meters["calm"] = 1

    world.para()
    world.say(
        f"{child.name} ate the slice slowly, then tucked the {params.instrument} under a chin and drew the bow across the string."
    )
    world.say(
        f"The note was no longer a warning; it was a plan."
    )
    world.say(
        f"By the end, {child.name} and {adult.name} were smiling in {params.place}, "
        f"and the little afternoon had turned into something steadier and kinder."
    )

    world.facts.update(
        child=child,
        adult=adult,
        cello=cello,
        snack=snack,
        note=note,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a gentle slice-of-life story about {p.child_name} and {p.adult_name} in {p.place} with a {p.instrument}.",
        f"Tell a story where a {p.misunderstanding} note causes a small misunderstanding, then becomes a better plan.",
        f"Write a child-friendly story including {p.snack}, {p.instrument}, and a quiet conversation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    adult = world.facts["adult"]
    return [
        QAItem(
            question=f"Who wanted to play the {p.instrument} in the story?",
            answer=f"{child.name} wanted to play the {p.instrument}."
        ),
        QAItem(
            question=f"What did {adult.name} worry about at first?",
            answer=f"{adult.name} worried about the {p.misunderstanding} note on the counter and the snack’s calories."
        ),
        QAItem(
            question="What changed after they talked?",
            answer=f"The note turned into a plan, and the afternoon became calmer because they understood each other."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cello?",
            answer="A cello is a string instrument that you play with a bow, and it has a deep, rich sound."
        ),
        QAItem(
            question="What is a calorie?",
            answer="A calorie is a unit used to talk about energy in food and drinks."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think something means one thing, but it really means something else."
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for person in world.people.values():
        lines.append(f"  {person.name}: role={person.role} meters={person.meters} memes={person.memes}")
    for obj in world.objects.values():
        lines.append(f"  {obj.name}: label={obj.label} meters={obj.meters} memes={obj.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(child_name="Mina", adult_name="Jules", place="the little kitchen", snack="apple cake", instrument="cello", misunderstanding="calorie", transformation="recipe card"),
    StoryParams(child_name="Noor", adult_name="Tessa", place="the sunny apartment", snack="banana bread", instrument="practice cello", misunderstanding="calories", transformation="shopping list"),
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/7."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/7."))
        print(sorted(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
