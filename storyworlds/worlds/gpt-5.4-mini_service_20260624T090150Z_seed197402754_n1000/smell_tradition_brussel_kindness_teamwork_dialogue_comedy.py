#!/usr/bin/env python3
"""
A comedy-leaning storyworld about a family tradition, a strong smell, and a
teamwork fix around brussel sprouts.

Premise:
A child helps prepare the yearly "special dinner" tradition, but the brussel
sprouts smell so strong that everyone complains.

Turn:
The child suggests a teamwork plan: divide the work, add friendly dialogue,
and make the sprouts taste better instead of throwing the dish away.

Resolution:
Kindness and teamwork turn the cooking into a funny, warm family moment, and
the dinner ends with the sprouts proudly on the table.
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
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    trait: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def display(self) -> str:
        return self.label or self.id


@dataclass
class Dish:
    id: str
    label: str
    smell: str
    tradition: str
    improved_by: str
    requires: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    name: str
    helper: str
    setting: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: str
    people: dict[str, Person] = field(default_factory=dict)
    dish: Optional[Dish] = None
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, person: Person) -> Person:
        self.people[person.id] = person
        return person

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "kitchen": "the kitchen",
    "backyard": "the backyard",
    "community hall": "the community hall",
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "grandma": "grandma",
    "grandpa": "grandpa",
    "sibling": "sibling",
}

DISHES = {
    "brussel_sprouts": Dish(
        id="brussel_sprouts",
        label="brussel sprouts",
        smell="strong",
        tradition="the yearly family dinner tradition",
        improved_by="butter and a little lemon",
        requires={"kindness", "teamwork", "dialogue"},
        tags={"smell", "tradition", "brussel", "kindness", "teamwork", "dialogue", "comedy"},
    )
}

NAMES = ["Mina", "Leo", "Ruby", "Theo", "Sana", "Owen", "Ivy", "Nico"]
TRAITS = ["curious", "cheerful", "quick-thinking", "patient", "goofy"]


ASP_RULES = r"""
has_smell(dish) :- brussel(dish).
needs_teamwork(dish) :- has_smell(dish).
needs_kindness(dish) :- needs_teamwork(dish).
needs_dialogue(dish) :- needs_teamwork(dish).
good_outcome(dish) :- has_smell(dish), needs_teamwork(dish), needs_kindness(dish), needs_dialogue(dish).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("brussel", "dish"),
            asp.fact("tradition", "dish"),
            asp.fact("smell", "dish"),
            asp.fact("kindness", "dish"),
            asp.fact("teamwork", "dish"),
            asp.fact("dialogue", "dish"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show good_outcome/1.")
    model = asp.one_model(program)
    atoms = sorted(set(asp.atoms(model, "good_outcome")))
    if atoms == [("dish",)]:
        print("OK: ASP gate matches the Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP gate did not prove the expected outcome.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about brussel sprouts and teamwork.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--setting", choices=SETTINGS)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(list(HELPERS)),
        setting=args.setting or rng.choice(list(SETTINGS)),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting == "backyard" and params.helper == "grandpa":
        return
    if params.name == params.helper:
        raise StoryError("The child and helper need to be different characters.")
    if params.setting not in SETTINGS:
        raise StoryError("That setting is not available.")
    if params.helper not in HELPERS:
        raise StoryError("That helper is not available.")


def build_world(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.setting])
    child = world.add(Person(id=params.name, label=params.name, trait=rng_trait(params.name)))
    helper = world.add(Person(id=params.helper, label=HELPERS[params.helper], trait="helpful"))
    dish = DISHES["brussel_sprouts"]
    world.dish = dish
    world.facts = {"child": child, "helper": helper, "dish": dish, "params": params}
    return world


def rng_trait(name: str) -> str:
    return TRAITS[sum(ord(c) for c in name) % len(TRAITS)]


def tell(world: World) -> None:
    f = world.facts
    child: Person = f["child"]
    helper: Person = f["helper"]
    dish: Dish = f["dish"]
    params: StoryParams = f["params"]

    world.say(
        f"{child.display} loved {dish.tradition}, because it meant everyone gathered in {world.setting}."
    )
    world.say(
        f"Every year, the same funny thing happened: the brussel sprouts filled the room with a smell so strong that even the spoon seemed to lean away."
    )
    world.para()
    world.say(
        f"That evening, {helper.display} peeked into the pot and said, \"Phew, that smell could wake up a sleepy sock.\""
    )
    world.say(
        f"{child.display} giggled and said, \"Then we need teamwork, not panic.\""
    )
    world.say(
        f"{child.display} stirred while {helper.display} chopped, and they added {dish.improved_by} together."
    )
    world.para()
    world.say(
        f"{helper.display} smiled and said, \"Kindness first. If we laugh at the smell, it stops bossing us around.\""
    )
    world.say(
        f"{child.display} nodded. \"And dialogue second,\" {child.display} said. \"I talk, you taste, and nobody runs away.\""
    )
    world.say(
        f"So they kept working side by side, and the kitchen turned from stink-and-sulk to chop-and-chuckle."
    )
    world.para()
    world.say(
        f"At dinner, the brussel sprouts came to the table looking brave instead of bossy."
    )
    world.say(
        f"Everyone tried a bite, made a dramatic face for fun, then laughed because the sprouts were actually tasty."
    )
    world.say(
        f"In the end, {child.display} had saved {dish.tradition} with kindness, teamwork, and just enough dialogue to keep the whole family smiling."
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Person = f["child"]
    helper: Person = f["helper"]
    dish: Dish = f["dish"]
    return [
        QAItem(
            question=f"What family tradition was being followed in the story?",
            answer=f"They were making {dish.label} for {dish.tradition}.",
        ),
        QAItem(
            question=f"Why did everyone react so much to the food?",
            answer=f"Because the {dish.label} gave off a strong smell that made the kitchen feel silly and overwhelming.",
        ),
        QAItem(
            question=f"What plan helped the family finish the meal?",
            answer=f"{child.display} and {helper.display} used kindness, teamwork, and dialogue to work together and improve the {dish.label}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are brussel sprouts?",
            answer="Brussel sprouts are small round vegetables that grow on a stalk and can be cooked for dinner.",
        ),
        QAItem(
            question="Why is teamwork helpful in a kitchen?",
            answer="Teamwork helps people share jobs, move faster, and fix problems together without getting overwhelmed.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, considerate, and helpful to other people.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is people talking to each other and listening so they can understand what to do next.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Person = f["child"]
    helper: Person = f["helper"]
    dish: Dish = f["dish"]
    return [
        f"Write a funny children's story about {child.display}, {helper.display}, and {dish.label}.",
        f"Tell a short comedy story where a family tradition goes slightly wrong because of a smell, then gets fixed with teamwork.",
        f"Write a gentle story that includes kindness, teamwork, and dialogue while making brussel sprouts for dinner.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for person in world.people.values():
        lines.append(f"  {person.id}: label={person.label!r} trait={person.trait!r}")
    if world.dish:
        lines.append(f"  dish: {world.dish.label} smell={world.dish.smell} tradition={world.dish.tradition}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell(world)
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
    StoryParams(name="Mina", helper="mother", setting="kitchen"),
    StoryParams(name="Leo", helper="grandma", setting="community hall"),
    StoryParams(name="Ruby", helper="father", setting="backyard"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_outcome/1."))
        print(sorted(set(asp.atoms(model, "good_outcome"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            p = sample.params
            header = f"### {p.name} with {p.helper} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
