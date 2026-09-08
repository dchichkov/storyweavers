#!/usr/bin/env python3
"""
A tall tale about an inhabitant of a garage whose enormous problem ends happily.

The garage is a small world of typed inhabitants and tools. A proud inhabitant
tries to fix a runaway bicycle bell, discovers that a neighbor's help matters,
and turns a noisy mess into a joyful garage parade.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = "garage"
    held_by: Optional[str] = None
    owner: Optional[str] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    inhabitant: str
    helper: str
    object_name: str
    garage: str = "the old garage"
    seed: Optional[int] = None


INHABITANTS = ["Luna", "Milo", "Pip", "Tess", "Bram", "Cora", "Nell", "Otis"]
OBJECTS = [
    ("brass bell", "a brass bicycle bell"),
    ("red wagon", "a red wagon"),
    ("blue toolbox", "a blue toolbox"),
    ("silver wheel", "a silver wheel"),
]
GARAGES = ["the old garage", "the wide garage", "the moonlit garage"]
HELPER_LINES = (
    '"A garage can hold a giant sound," said {helper}, "but it still needs two careful hands."',
    '"Do not wrestle the trouble alone," said {helper}. "Tell me where it is pulling."',
    '"Even the biggest tangle has a small beginning," said {helper}. "Let us find it together."',
)
OPENINGS = (
    "In {garage}, an inhabitant named {inhabitant} lived among ladders, jars, and shining tools.",
    "Everyone in {garage} knew {inhabitant}, the inhabitant who could lift a tire as easily as a teacup.",
    "At the back of {garage}, {inhabitant} kept watch over a marvelous collection of wheels and springs.",
)
REALIZATIONS = (
    "{inhabitant} finally understood that being strong was not the same as being wise.",
    "The tall tale had grown so large that {inhabitant} could no longer see its simple knot.",
    "{inhabitant} saw that a helper's question could reach places where mighty muscles could not.",
)


def object_phrase(label: str) -> str:
    return dict(OBJECTS).get(label, f"a {label}")


def build_world(params: StoryParams) -> World:
    if params.inhabitant == params.helper:
        raise StoryError("The inhabitant and helper must have different names.")
    if params.object_name not in {name for name, _ in OBJECTS}:
        raise StoryError(f"Unknown garage object: {params.object_name!r}.")

    world = World()
    inhabitant = world.add(
        Entity(
            params.inhabitant,
            "character",
            "inhabitant",
            "garage inhabitant",
            meters={"strength": 9.0, "balance": 4.0},
            memes={"pride": 4.0, "worry": 1.0, "joy": 1.0},
        )
    )
    helper = world.add(
        Entity(
            params.helper,
            "character",
            "neighbor",
            "helpful neighbor",
            meters={"patience": 8.0, "balance": 8.0},
            memes={"kindness": 6.0, "curiosity": 4.0, "joy": 2.0},
        )
    )
    thing = world.add(
        Entity(
            "garage_object",
            "thing",
            "tool",
            object_phrase(params.object_name),
            meters={"stability": 2.0, "noise": 7.0},
            memes={"importance": 5.0},
            owner=inhabitant.id,
        )
    )

    vals = {
        "garage": params.garage,
        "inhabitant": inhabitant.id,
        "helper": helper.id,
        "object": thing.label,
    }
    opening = OPENINGS[(params.seed or 0) % len(OPENINGS)]
    helper_line = HELPER_LINES[((params.seed or 0) // len(OPENINGS)) % len(HELPER_LINES)]
    realization = REALIZATIONS[((params.seed or 0) // (len(OPENINGS) * len(HELPER_LINES))) % len(REALIZATIONS)]

    world.say(opening.format(**vals))
    world.say(
        f"{inhabitant.id} was a famous inhabitant of the garage, tall in courage and taller in confidence. "
        "People said this inhabitant could tighten one hundred bolts before breakfast."
    )
    world.para()
    world.say(
        f"One morning, {thing.label} began rolling, rattling, and ringing around the garage "
        "as if a tiny storm had climbed onto wheels."
    )
    thing.meters["noise"] = 10.0
    thing.meters["stability"] = 0.0
    inhabitant.memes["worry"] = 6.0
    world.say(
        f"{inhabitant.id} chased it beneath a bench, over a rug, and up a ramp made from three boards. "
        "Each mighty grab only sent the runaway object on a grander adventure."
    )
    world.say(
        f"{helper.id} stepped into the garage doorway and watched the great chase "
        "make dust jump from the rafters."
    )
    world.say(helper_line.format(**vals))
    world.para()
    world.say(realization.format(**vals))
    world.say(
        f'"I was pushing at the whole problem," {inhabitant.id} admitted. '
        f'"Can you help me find the little part that started it?"'
    )
    world.say(
        f'"Gladly," {helper.id} replied. "You watch the wheel, and I will steady the handle."'
    )
    inhabitant.memes["pride"] = 1.0
    inhabitant.memes["trust"] = 7.0
    thing.held_by = helper.id
    world.say(
        f"Together they found one loose spring. {inhabitant.id} held {thing.label} still while "
        f"{helper.id} guided the spring back into its nest."
    )
    thing.meters["noise"] = 1.0
    thing.meters["stability"] = 10.0
    thing.held_by = inhabitant.id
    inhabitant.memes["relief"] = 8.0
    helper.memes["joy"] = 8.0
    world.say(
        f"The garage became quiet for one breath. Then {inhabitant.id} gave {thing.label} a careful tap, "
        "and it answered with one bright, friendly ring."
    )
    world.para()
    world.say(
        f"{inhabitant.id} laughed so loudly that a hanging raincoat waved. "
        f'"Thank you, {helper.id}. Your patience fixed what my strength could not."'
    )
    world.say(
        f'"And your strength made a fine anchor," {helper.id} said. "A happy ending is best when everyone helps build it."'
    )
    world.say(
        f"They rolled {thing.label} to the open garage door and led a tiny parade down the lane. "
        "Even the dust seemed to march in step."
    )
    world.say(
        f"That evening, {thing.label} rested safely on a shelf, while {inhabitant.id} and {helper.id} "
        "shared lemonade beneath the tallest ladder in the garage."
    )

    world.facts.update(
        inhabitant=inhabitant,
        helper=helper,
        object=thing,
        garage=params.garage,
        helper_line=helper_line.format(**vals),
        realization=realization.format(**vals),
        ending=f"{thing.label} rested safely on a shelf while {inhabitant.id} and {helper.id} shared lemonade beneath the tallest ladder in the garage.",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    inhabitant: Entity = f["inhabitant"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    thing: Entity = f["object"]  # type: ignore[assignment]
    return [
        f"Write a Tall Tale about an inhabitant named {inhabitant.id} in a garage.",
        f"Tell a child-friendly happy-ending story where {inhabitant.id} and {helper.id} repair {thing.label}.",
        f"Create a garage adventure with an enormous problem, a helpful neighbor, and a joyful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    inhabitant: Entity = f["inhabitant"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    thing: Entity = f["object"]  # type: ignore[assignment]
    return [
        QAItem(
            "Who was the inhabitant in the story?",
            f"{inhabitant.id} was the strong and proud inhabitant who lived among the tools in the garage.",
        ),
        QAItem(
            f"What went wrong with {thing.label}?",
            f"{thing.label.capitalize()} became unstable and noisy, rolling all around the garage while {inhabitant.id} tried to catch it.",
        ),
        QAItem(
            f"How did {helper.id} help?",
            f"{helper.id} steadied {thing.label} and helped {inhabitant.id} find and replace the loose spring.",
        ),
        QAItem(
            "What did the inhabitant learn?",
            f"{inhabitant.id} learned that strength alone was not enough; careful teamwork and a helper's patience could solve the problem.",
        ),
        QAItem(
            "How do we know the story had a happy ending?",
            str(f["ending"]),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a garage?",
            "A garage is a building or space where vehicles, tools, and useful objects can be stored or repaired.",
        ),
        QAItem(
            "What is an inhabitant?",
            "An inhabitant is a person or creature that lives in a particular place.",
        ),
        QAItem(
            "Why can teamwork help with a difficult job?",
            "Teamwork helps because people can share different skills, notice different details, and support one another.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tall Tale garage story world.")
    parser.add_argument("--inhabitant")
    parser.add_argument("--helper")
    parser.add_argument("--object", dest="object_name", choices=[n for n, _ in OBJECTS])
    parser.add_argument("--garage", choices=GARAGES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    inhabitant = args.inhabitant or rng.choice(INHABITANTS)
    choices = [name for name in INHABITANTS if name != inhabitant]
    helper = args.helper or rng.choice(choices)
    return StoryParams(
        inhabitant=inhabitant,
        helper=helper,
        object_name=args.object_name or rng.choice([n for n, _ in OBJECTS]),
        garage=args.garage or rng.choice(GARAGES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: type={entity.type}, location={entity.location}, "
            f"meters={entity.meters}, memes={entity.memes}, held_by={entity.held_by}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== world qa =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


ASP_RULES = r"""
garage(garage).
character(X) :- inhabitant(X).
character(X) :- helper(X).
thing(X) :- object(X).
steady(X) :- repaired(X).
happy_ending(I,H,O) :- inhabitant(I), helper(H), object(O), repaired(O), teamwork(I,H).
teamwork(I,H) :- inhabitant(I), helper(H).
#show happy_ending/3.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("garage", "garage")]
    for name in INHABITANTS:
        lines.append(asp.fact("inhabitant", name))
        lines.append(asp.fact("helper", name))
    for name, _ in OBJECTS:
        lines.append(asp.fact("object", name))
    lines.append(asp.fact("repaired", "brass_bell"))
    lines.append(asp.fact("repaired", "red_wagon"))
    lines.append(asp.fact("repaired", "blue_toolbox"))
    lines.append(asp.fact("repaired", "silver_wheel"))
    return "\n".join(lines)


def asp_program(show: str = "#show happy_ending/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program(), models=1)
    if not models:
        print("ASP verification failed: no model.")
        return 1
    atoms = asp.atoms(models[0], "happy_ending")
    if not atoms:
        print("ASP verification failed: no happy ending atom.")
        return 1
    for seed in range(5):
        params = StoryParams("Luna", "Milo", "brass bell", seed=seed)
        sample = generate(params)
        if "happy ending" not in sample.story.lower():
            print("Python verification failed: missing happy ending.")
            return 1
        if not sample.story_qa:
            print("Python verification failed: missing story QA.")
            return 1
    print("OK: Python stories and ASP twin verified.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, (object_name, _) in enumerate(OBJECTS):
            samples.append(
                generate(
                    StoryParams(
                        inhabitant=INHABITANTS[index],
                        helper=INHABITANTS[(index + 1) % len(INHABITANTS)],
                        object_name=object_name,
                        garage=GARAGES[index % len(GARAGES)],
                        seed=base_seed + index,
                    )
                )
            )
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(json.dumps({"asp_atoms": [str(atom) for atom in model]}, indent=2))
        return

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
