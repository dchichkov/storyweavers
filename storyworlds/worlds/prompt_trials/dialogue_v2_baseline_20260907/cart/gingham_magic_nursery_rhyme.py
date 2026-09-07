#!/usr/bin/env python3
"""Gingham Magic: a nursery-rhyme tale about a little cart and a helping cloth."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Pip"
    helper: str = "Dot"
    color: str = "red"
    object_name: str = "apples"
    problem: str = "mud"
    spell: str = "kindness"
    seed: int = 777


COLORS = ("red", "blue", "green", "yellow")
OBJECTS = {
    "apples": ("apples", "orchard"),
    "bells": ("bells", "schoolhouse"),
    "flowers": ("flowers", "cottage"),
}
PROBLEMS = {
    "mud": "lift",
    "hill": "pull",
    "rain": "cover",
}
SPELLS = {
    "lift": "kindness",
    "pull": "kindness",
    "cover": "kindness",
}
NAMES = ("Pip", "Dot", "Mabel", "Toby", "Nell", "Bram")


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", "lane",
                           memes={"hope": 0.7, "courage": 0.5}),
            "helper": Entity("helper", params.helper, "character", "lane",
                             memes={"hope": 0.7, "courage": 0.7}),
            "cart": Entity("cart", "the little cart", "vehicle", "barn",
                           meters={"load": 0, "capacity": 2, "distance": 0}),
            "cloth": Entity("cloth", f"the {params.color}-and-white gingham cloth",
                            "magic_cloth", "barn",
                            meters={"sparkles": 3}, memes={"kindness": 1.0}),
            "cargo": Entity("cargo", params.object_name, "cargo", "orchard",
                            meters={"units": 2, "delivered": 0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = ""):
        self.history.append(Event(kind, text, question, cause, result, self.snapshot()))

    def magic(self, action: str):
        cloth = self.entities["cloth"]
        cart = self.entities["cart"]
        if action not in ("lift", "pull", "cover"):
            raise StoryError("The gingham cloth knows only a gentle useful magic.")
        if cloth.meters["sparkles"] <= 0:
            raise StoryError("The gingham cloth has no sparkle left for that spell.")
        cloth.meters["sparkles"] -= 1
        if action == "lift":
            cart.meters["load"] = min(cart.meters["capacity"], cart.meters["load"] + 1)
        elif action == "pull":
            cart.meters["distance"] += 2
        else:
            cloth.location = "over_cart"

    def deliver(self, units: int):
        cart = self.entities["cart"]
        cargo = self.entities["cargo"]
        if units <= 0 or units > cargo.meters["units"] - cargo.meters["delivered"]:
            raise StoryError("The cart cannot deliver cargo that is not there.")
        if cart.meters["load"] < units:
            raise StoryError("The cart must be loaded before it can deliver.")
        cargo.meters["delivered"] += units
        cart.meters["load"] -= units
        cart.location = self.params.object_name + "_destination"
        cargo.location = cart.location if cargo.meters["delivered"] == cargo.meters["units"] else cargo.location

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history if event.question
            ],
            world_qa=[
                QAItem("What was the gingham cloth used for?",
                       "It used gentle magic to help the little cart carry its load."),
                QAItem("Why did the friends work together?",
                       "Their kindness made the cloth's magic work."),
            ],
            world=self,
        )


PROMPT = "Write a gentle nursery-rhyme story about a little cart, a gingham cloth, and friends who solve a delivery problem with kindness."


def validate_params(params: StoryParams):
    if params.color not in COLORS:
        raise StoryError("Choose a simple gingham color.")
    if params.object_name not in OBJECTS:
        raise StoryError("Choose apples, bells, or flowers.")
    if params.problem not in PROBLEMS:
        raise StoryError("Choose mud, hill, or rain.")
    if params.spell != PROBLEMS[params.problem]:
        raise StoryError("That spell does not match the problem.")
    if params.hero == params.helper:
        raise StoryError("The two friends need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.helper)):
        raise StoryError("Names should be simple, such as Pip and Dot.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["cargo"].label = OBJECTS[params.object_name][0]
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    helper = world.entities["helper"].label
    cloth = world.entities["cloth"].label
    cargo = OBJECTS[params.object_name][0]
    destination = OBJECTS[params.object_name][1]

    world.narrate(
        "beginning",
        f"{hero} had a little cart, and {helper} had a bright {cloth}. "
        f"At dawn they found two baskets of {cargo} waiting by the barn."
    )
    world.narrate(
        "plan",
        f"“We must take them to the {destination},” said {hero}. "
        f"“But the road has a trouble today.”"
    )

    if params.problem == "mud":
        world.narrate(
            "problem",
            "The lane was thick with brown mud. The cart wheels sank with a squelch, "
            "and the baskets rocked from side to side.",
            question="Why could the cart not roll easily?",
            cause="The lane was deep and muddy.",
            result="Its wheels sank instead of carrying the baskets onward.",
        )
        world.narrate("try", f"{helper} tugged the handle. “Pull, little cart! Pull!”")
        world.entities["helper"].memes["courage"] += 0.2
        world.magic("lift")
        world.narrate(
            "magic",
            f"{hero} spread the {cloth} beneath one basket and {helper} called, "
            "“Please, kind cloth, help us lift!” Up sprang the basket, light as a feather.",
            question="How did the gingham cloth help?",
            cause="The friends asked it kindly to lift one basket.",
            result="Its magic made the basket light enough for the cart.",
        )
        world.entities["cart"].meters["load"] = 1
        world.deliver(1)
        world.magic("lift")
        world.entities["cart"].meters["load"] = 1
        world.deliver(1)
        world.narrate(
            "resolution",
            f"One basket, then two, rolled safely to the {destination}. "
            f"The muddy wheels left a row of round prints behind.",
            question="How did all the {cargo} reach the destination?",
            cause="The cloth lifted each basket so the cart could carry it through the mud.",
            result=f"Both baskets arrived safely at the {destination}.",
        )
    elif params.problem == "hill":
        world.narrate(
            "problem",
            "The road rose up a steep green hill. The cart groaned, “Oh dear, oh me,” "
            "and stopped beneath a hawthorn tree.",
            question="Why did the cart stop?",
            cause="The road climbed a steep hill.",
            result="The loaded cart could not roll upward by itself.",
        )
        world.entities["cart"].meters["load"] = 2
        world.narrate("try", f"{hero} pushed, and {helper} pulled, but the cart would not budge.")
        world.magic("pull")
        world.narrate(
            "magic",
            f"They tied the {cloth} to the handle and sang, “Kind hearts pull, "
            "and wheels roll true!” The gingham cloth shimmered in the sun.",
            question="What made the cart begin moving?",
            cause="The friends joined their effort with the cloth's kindness spell.",
            result="The cart rolled up the hill instead of slipping backward.",
        )
        world.entities["cart"].meters["distance"] += 2
        world.deliver(2)
        world.narrate(
            "resolution",
            f"Up, up, up they went, and down the other side to the {destination}. "
            f"The cloth fluttered like a tiny flag above the cart.",
            question="Where did the cart take the baskets?",
            cause="The friends pulled together over the steep hill.",
            result=f"They delivered both baskets to the {destination}.",
        )
    else:
        world.narrate(
            "problem",
            "Gray clouds gathered overhead. Plip, plop, raindrops fell upon the baskets.",
            question="What danger threatened the cargo?",
            cause="Rain began falling from the gray clouds.",
            result="The baskets could become wet before reaching their destination.",
        )
        world.entities["cart"].meters["load"] = 2
        world.magic("cover")
        world.narrate(
            "magic",
            f"{hero} spread the {cloth} over the cart. It grew wide and bright, "
            "making a snug little roof while {helper} held the corners.",
            question="How did the friends keep the baskets dry?",
            cause="They stretched the magical gingham cloth over the cart.",
            result="The cloth became a roof that kept the rain away.",
        )
        world.deliver(2)
        world.narrate(
            "resolution",
            f"Drip, drop, drip, they reached the {destination}. "
            f"Not one {cargo[:-1] if cargo.endswith('s') else cargo} was wet, "
            "and the cloth folded back to its small square shape.",
            question="What showed that the rain spell worked?",
            cause="The gingham cloth covered the cart like a roof.",
            result=f"Both baskets arrived dry at the {destination}.",
        )

    world.narrate(
        "ending",
        f"Then {hero} and {helper} shared a song beside the little cart. "
        f"The {cloth} rested on its handle, red-and-white checks glowing softly. "
        "Kindness had made the magic, and the magic had helped kindness along."
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    validate_params(sample.params)
    cargo = world.entities["cargo"]
    if cargo.meters["delivered"] != cargo.meters["units"]:
        raise StoryError("Every basket must reach its destination.")
    if world.entities["cart"].meters["load"] != 0:
        raise StoryError("The cart must be empty at the ending.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs several grounded questions.")
    if len(sample.story.split()) < 100:
        raise StoryError("The story needs a complete beginning, turn, and ending.")
    if "gingham" not in sample.story.lower():
        raise StoryError("The story must include gingham.")
    if "magic" not in sample.story.lower() and "magical" not in sample.story.lower():
        raise StoryError("The story must include magic.")
    if not sample.story.rstrip().endswith("along."):
        raise StoryError("The story needs a clear closing image.")


ASP_RULES = """
valid_problem(P,S) :- problem(P,S).
#show valid_problem/2.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(fact("problem", problem, spell)
                     for problem, spell in PROBLEMS.items())


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid_problem"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--color", choices=COLORS)
    parser.add_argument("--object-name", choices=tuple(OBJECTS))
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--spell", choices=tuple(SPELLS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    problem = args.problem or rng.choice(tuple(PROBLEMS))
    spell = args.spell or PROBLEMS[problem]
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        helper=helper,
        color=args.color or rng.choice(COLORS),
        object_name=args.object_name or rng.choice(tuple(OBJECTS)),
        problem=problem,
        spell=spell,
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if asp_combos() != set(PROBLEMS.items()):
        raise StoryError("Python and ASP disagree about the available spells.")
    tested = 0
    for problem, spell in PROBLEMS.items():
        for color in COLORS:
            for object_name in OBJECTS:
                sample = generate(StoryParams(problem=problem, spell=spell,
                                               color=color, object_name=object_name))
                check_sample(sample)
                tested += 1
    print(f"OK: {tested} story states; ASP agrees on {len(SPELLS)} spells.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "entities": sample.world.snapshot(),
            "history": [asdict(event) for event in sample.world.history],
        }, indent=2))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = []
            for problem, spell in PROBLEMS.items():
                if args.problem and args.problem != problem:
                    continue
                if args.spell and args.spell != spell:
                    continue
                copied = argparse.Namespace(**vars(args))
                copied.problem = problem
                copied.spell = spell
                params_list.append(resolve_params(copied, rng))
            if not params_list:
                raise StoryError("No combinations match those options.")
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
