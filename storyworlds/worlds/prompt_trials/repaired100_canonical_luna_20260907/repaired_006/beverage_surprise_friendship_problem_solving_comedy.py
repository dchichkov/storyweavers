#!/usr/bin/env python3
"""
A cheerful beverage surprise in which two friends solve a fizzy little problem.
"""

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
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


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
    fired: set[str] = field(default_factory=set)
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


BEVERAGES = (
    ("sparkling berry lemonade", "red bubbles"),
    ("peach fizz", "golden foam"),
    ("minty apple cooler", "green leaves"),
    ("chocolate banana shake", "a very serious mustache of foam"),
    ("blueberry oat smoothie", "purple swirls"),
)

PLACES = (
    "the sunny park picnic table",
    "the community garden bench",
    "the little street fair",
    "the school courtyard",
    "the clubhouse porch",
)

SURPRISES = (
    "a paper umbrella popped out of the cup",
    "the straw squeaked like a tiny duck",
    "a hidden lemon slice bobbed to the surface",
    "the lid wore a cheerful sticker crown",
    "the first sip made a bubble shaped like a heart",
)

PROBLEMS = (
    "the wind rolled the drink toward a puddle",
    "the straw vanished beneath a napkin mountain",
    "the lid began wobbling like a dancing hat",
    "two identical cups got mixed up",
    "the ice cubes jammed the straw shut",
)

ENDINGS = (
    "They toasted their teamwork, though the paper umbrella landed on Rowan's nose.",
    "The friends drank carefully while the straw gave one final proud squeak.",
    "Their laughter shook the table, and the heart-shaped bubble floated away.",
    "They labeled the cups, then laughed when the label stuck to a passing leaf.",
    "The drink was saved, the snack was shared, and nobody trusted the dancing lid again.",
)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    friend_one: str = "Luna"
    friend_two: str = "Milo"
    beverage: str = BEVERAGES[0][0]
    garnish: str = BEVERAGES[0][1]
    place: str = PLACES[0]
    surprise: str = SURPRISES[0]
    problem: str = PROBLEMS[0]
    ending: str = ENDINGS[0]


def _validate(params: StoryParams) -> None:
    if not params.friend_one.strip() or not params.friend_two.strip():
        raise StoryError("Friends need names before they can share a beverage.")
    if params.friend_one == params.friend_two:
        raise StoryError("The two friends must have different names.")
    if not params.beverage.strip():
        raise StoryError("The beverage cannot be empty.")
    if not params.problem.strip() or not params.surprise.strip():
        raise StoryError("A comedy problem and a surprise are both required.")


def tell(params: StoryParams) -> World:
    _validate(params)
    world = World()
    luna = world.add(Entity("friend_one", "character", params.friend_one, memes={"friendship": 1.0}))
    milo = world.add(Entity("friend_two", "character", params.friend_two, memes={"friendship": 1.0}))
    drink = world.add(Entity("beverage", "beverage", params.beverage, meters={"fullness": 1.0, "safety": 1.0}))
    world.facts.update(
        friend_one=luna,
        friend_two=milo,
        beverage=drink,
        place=params.place,
        garnish=params.garnish,
        surprise=params.surprise,
        problem=params.problem,
        ending=params.ending,
    )

    world.say(
        f"At {params.place}, {params.friend_one} brought a {params.beverage} "
        f"decorated with {params.garnish} for {params.friend_two}."
    )
    world.say(
        f'"Surprise!" said {params.friend_one}. "It is a friendship beverage, so it has to be shared."'
    )
    world.say(f'"Does it come with a friendship napkin?" asked {params.friend_two}.')
    world.say(
        f'"Only if you promise not to wear it as a hat," said {params.friend_one}. '
        f"Then {params.surprise}."
    )

    world.para()
    world.say(f"Before either friend could sip, {params.problem}.")
    world.say(
        f'"I have a plan," said {params.friend_two}. "You hold the cup, and I will rescue the useful parts."'
    )
    world.say(
        f'"That sounds clever," said {params.friend_one}. "Or at least less wobbly than the lid."'
    )
    world.say(
        f"They worked together: {params.friend_one} steadied the beverage while "
        f"{params.friend_two} used a napkin, a spoon, and excellent sideways thinking."
    )
    world.fired.add("problem_solved")
    drink.meters["safety"] = 2.0
    drink.meters["fullness"] = 0.9
    luna.memes["confidence"] = 1.0
    milo.memes["confidence"] = 1.0

    world.para()
    world.say(
        f"The plan worked. The {params.beverage} was safe, the surprise was still surprising, "
        f"and both friends took a careful sip."
    )
    world.say(f'"That was delicious," said {params.friend_two}.')
    world.say(f'"And very educational," said {params.friend_one}. "We learned never to challenge a lid."')
    world.say(params.ending)
    return world


ASP_RULES = r"""
beverage(berry_drink).
friends(luna,milo).
surprise_ready(berry_drink).
problem(wobble).
solution(hold_and_rescue).

solved(berry_drink) :-
    beverage(berry_drink),
    friends(luna,milo),
    surprise_ready(berry_drink),
    problem(wobble),
    solution(hold_and_rescue).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        (
            asp.fact("beverage", "berry_drink"),
            asp.fact("friends", "luna", "milo"),
            asp.fact("surprise_ready", "berry_drink"),
            asp.fact("problem", "wobble"),
            asp.fact("solution", "hold_and_rescue"),
        )
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    solved = asp.atoms(model, "solved")
    if solved == [("berry_drink",)]:
        print("OK: ASP and Python agree that the beverage problem is solved.")
        return 0
    print("MISMATCH: ASP did not find the expected solution.")
    print(solved)
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    seed = int(args.seed if args.seed is not None else 0)
    names = (("Luna", "Milo"), ("Pia", "Bo"), ("Nia", "Toby"), ("Zoe", "Finn"))
    first, second = names[seed % len(names)]
    beverage, garnish = rng.choice(BEVERAGES)
    return StoryParams(
        seed=seed,
        friend_one=first,
        friend_two=second,
        beverage=beverage,
        garnish=garnish,
        place=rng.choice(PLACES),
        surprise=rng.choice(SURPRISES),
        problem=rng.choice(PROBLEMS),
        ending=rng.choice(ENDINGS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a funny friendship story about {f['friend_one'].label} surprising {f['friend_two'].label} with a {f['beverage'].label}.",
        f"Include a beverage problem at {f['place']} and show the friends solving it together.",
        "End with a warm, comic image that proves the friends succeeded.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["friend_one"].label
    b = f["friend_two"].label
    drink = f["beverage"].label
    return [
        QAItem(
            question=f"Who prepared the surprise beverage for {b}?",
            answer=f"{a} prepared the {drink} as a friendship surprise for {b}.",
        ),
        QAItem(
            question="What problem happened to the beverage?",
            answer=f"The problem was that {f['problem']}.",
        ),
        QAItem(
            question=f"How did {a} and {b} solve the problem?",
            answer=f"{a} steadied the beverage while {b} used a napkin, a spoon, and careful sideways thinking to rescue it.",
        ),
        QAItem(
            question="What showed that the friends were happy at the end?",
            answer=f"They shared the safe beverage, laughed together, and finished with this comic moment: {f['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beverage?",
            answer="A beverage is a drink, such as water, juice, tea, milk, or a smoothie.",
        ),
        QAItem(
            question="Why can teamwork help solve a problem?",
            answer="Teamwork lets people combine their ideas and actions, so one person can help steady or improve what another person is doing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A comic beverage friendship storyworld.")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 1 if args.all else max(0, args.n)
    samples = []
    for index in range(count):
        seed = base_seed + index
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
