#!/usr/bin/env python3
"""
A small animal story world about lava, repetition, and a careful rescue.

A young animal notices lava creeping toward the meadow. At first, the warning
is repeated so often that the others stop listening. A turn comes when a tiny
animal follows the repeated warning to a safe path, and the group works
together to reach a cool stream. The ending image shows a changed meadow and
animals who now listen when a true warning is repeated.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("warmth", "fear", "tired", "safe", "distance"):
            self.meters.setdefault(key, 0.0)
        for key in ("trust", "attention", "courage", "care"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    rabbit: str
    tortoise: str
    bird: str
    hill: str = "the green hill"
    seed: Optional[int] = None
    warning_word: str = "lava"
    repetition: int = 3
    variation: int = 0


@dataclass(frozen=True)
class Route:
    name: str
    clue: str
    action: str
    ending: str


ROUTES = [
    Route(
        "fern_path",
        "The ferns bent away from the heat, making a narrow path toward the stream.",
        "They followed the bent ferns in a slow line, with the bird flying ahead.",
        "At the stream, cool water curled around their feet while the lava stopped behind the stones.",
    ),
    Route(
        "stone_steps",
        "Three pale stones made steps across a patch of ash and pointed downhill.",
        "The tortoise tested each stone before the others crossed it.",
        "The animals reached the stream just as a red glow filled the old path behind them.",
    ),
    Route(
        "bird_shadow",
        "The bird saw that the safest ground lay beneath a row of tall blue trees.",
        "They moved from shadow to shadow, keeping together and never stepping on the glowing earth.",
        "The blue trees stood between the friends and the lava, and the stream sang below them.",
    ),
    Route(
        "rain_pool",
        "A little rain pool remained beside the hill, and damp soil circled it like a ring.",
        "The rabbit led everyone around the damp ring toward the cooler valley.",
        "Mud cooled the edge of the flow, and the friends waited safely beside the valley stream.",
    ),
]

NAMES = ["Luna", "Milo", "Pip", "Clover", "Nori", "Tess", "Bram", "Wren"]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def setup_world(params: StoryParams) -> World:
    world = World(params)
    world.add(Entity(params.rabbit, "animal", params.rabbit, "meadow"))
    world.add(Entity(params.tortoise, "animal", params.tortoise, "meadow"))
    world.add(Entity(params.bird, "animal", params.bird, "meadow"))
    world.add(Entity("lava", "hazard", "lava", "volcano"))
    world.add(Entity("stream", "place", "cool stream", "valley"))
    return world


def tell_story(world: World) -> None:
    p = world.params
    rabbit = world.entities[p.rabbit]
    tortoise = world.entities[p.tortoise]
    bird = world.entities[p.bird]
    lava = world.entities["lava"]
    route = ROUTES[p.variation % len(ROUTES)]

    world.say(
        f"{p.rabbit} the rabbit lived with {p.tortoise} the tortoise and "
        f"{p.bird} the bird on {p.hill}."
    )
    world.say(
        f"One bright morning, {p.rabbit} smelled smoke and saw {p.warning_word} "
        "shining far away."
    )
    world.say(
        f'"Lava! Lava! Lava!" cried {p.rabbit}. '
        f'"{p.warning_word} is coming down the mountain!"'
    )
    rabbit.memes["courage"] += 1
    rabbit.memes["attention"] += 1
    lava.meters["distance"] = 8

    world.para()
    world.say(
        f"{p.tortoise} looked up from a patch of clover. "
        f'"You say "{p.warning_word}" every day," said {p.tortoise}. '
        '"Perhaps it is only a story."'
    )
    world.say(
        f'{p.bird} flapped onto a branch. "Lava, lava," sang {p.bird}, '
        '"but the song sounded like a game."'
    )
    world.say(
        f"{p.rabbit} stamped one small foot. "
        f'"Listen, please. The {p.warning_word} is closer now."'
    )
    tortoise.memes["attention"] -= 0.5
    bird.memes["attention"] -= 0.5
    rabbit.meters["fear"] += 1
    lava.meters["distance"] = 5

    world.para()
    world.say(
        f"Then the ground gave a warm little shiver. "
        f"{p.tortoise} felt heat beneath the clover, and {p.bird} saw a red line "
        "curling between the rocks."
    )
    world.say(
        f'"Lava!" said {p.rabbit}. "Lava, lava, lava!"'
    )
    world.say(
        f'"Now I hear you," said {p.tortoise}. "Show us what you saw."'
    )
    world.say(
        f'"I can see a way!" called {p.bird}. "Follow my shadow, but stay together."'
    )
    tortoise.memes["attention"] += 1
    bird.memes["attention"] += 1
    tortoise.memes["trust"] += 1
    bird.memes["trust"] += 1
    lava.meters["distance"] = 3

    world.para()
    world.say(route.clue)
    world.say(route.action)
    world.say(
        f'{p.rabbit} called, "Lava behind us!" '
        f'{p.tortoise} answered, "We are safe if we keep moving." '
        f'{p.bird} repeated, "Together, together!"'
    )
    route_action = route.action
    for animal in (rabbit, tortoise, bird):
        animal.location = "valley"
        animal.meters["safe"] = 1
        animal.memes["care"] += 1
        animal.memes["trust"] += 0.5
    lava.meters["distance"] = 0
    lava.meters["warmth"] = 3
    world.say(route.ending)

    world.para()
    world.say(
        f"The next morning, {p.rabbit} repeated the warning once more, but this "
        "time the others listened at once."
    )
    world.say(
        f"{p.tortoise} nodded. " '"A repeated word can still be important."'
    )
    world.say(
        f"{p.bird} flew over the blackened meadow and called, "
        '"Listen, care, and move together!"'
    )
    world.say(
        "Below the hill, green shoots appeared beside the cool stream, while "
        "the old lava cooled into dark, quiet stones."
    )

    world.facts.update(
        rabbit=rabbit,
        tortoise=tortoise,
        bird=bird,
        lava=lava,
        route=route,
        route_action=route_action,
        ending=route.ending,
    )


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    route: Route = world.facts["route"]
    return [
        QAItem(
            "Which animals lived on the hill?",
            f"{p.rabbit} the rabbit, {p.tortoise} the tortoise, and {p.bird} the bird lived on the hill.",
        ),
        QAItem(
            "What danger did the rabbit see?",
            f"The rabbit saw lava coming down the mountain.",
        ),
        QAItem(
            "Why did the other animals ignore the first warning?",
            "They had heard the warning repeated before and thought it might only be a game or story.",
        ),
        QAItem(
            "What made the animals listen at last?",
            "The ground shivered, the tortoise felt heat, and the bird saw a red line of lava between the rocks.",
        ),
        QAItem(
            "How did the animals reach safety?",
            route.action,
        ),
        QAItem(
            "What changed by the end of the story?",
            "The animals learned that a repeated warning can still be important, and they reached the cool stream together.",
        ),
        QAItem(
            "What showed that the meadow could recover?",
            "Green shoots appeared beside the cool stream while the lava cooled into dark stones.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is lava?",
            "Lava is melted rock that flows from a volcano and is very hot.",
        ),
        QAItem(
            "Why should animals move away from lava?",
            "Animals should move away because lava is hot and can burn or trap them.",
        ),
        QAItem(
            "What does repetition mean?",
            "Repetition means saying or doing something again.",
        ),
        QAItem(
            "Why can a repeated warning matter?",
            "A repeated warning can matter because the danger may still be real even when it has been heard before.",
        ),
    ]


def generation_prompts() -> list[str]:
    return [
        "Write a child-facing animal story about a rabbit who repeats a warning about lava.",
        "Tell a simple animal tale in which repetition first seems annoying but then helps friends reach safety.",
        "Write an animal story with lava, a repeated warning, a turning point, and a hopeful ending.",
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal story world about lava and a repeated warning."
    )
    parser.add_argument("--rabbit")
    parser.add_argument("--tortoise")
    parser.add_argument("--bird")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    supplied = [args.rabbit, args.tortoise, args.bird]
    present = [name for name in supplied if name]
    if len(set(present)) != len(present):
        raise StoryError("The rabbit, tortoise, and bird must have different names.")
    if len(present) not in (0, 3):
        raise StoryError("Please provide all three animal names, or provide none.")
    if not present:
        names = rng.sample(NAMES, 3)
    else:
        names = present
    repetition = 3 + rng.randrange(2)
    return StoryParams(
        rabbit=names[0],
        tortoise=names[1],
        bird=names[2],
        seed=args.seed,
        repetition=repetition,
        variation=rng.randrange(1000000),
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: location={entity.location} meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
animal(rabbit).
animal(tortoise).
animal(bird).
hazard(lava).
place(stream).

warns(rabbit,lava).
repeated_warning(lava) :- warns(rabbit,lava).
hears(tortoise,lava) :- repeated_warning(lava).
hears(bird,lava) :- repeated_warning(lava).
safe(tortoise,stream) :- hears(tortoise,lava).
safe(bird,stream) :- hears(bird,lava).
safe(rabbit,stream) :- safe(tortoise,stream), safe(bird,stream).

#show repeated_warning/1.
#show safe/2.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("animal", "rabbit"),
            asp.fact("animal", "tortoise"),
            asp.fact("animal", "bird"),
            asp.fact("hazard", "lava"),
            asp.fact("place", "stream"),
            asp.fact("warns", "rabbit", "lava"),
        ]
    )


def asp_program(show: str = "#show repeated_warning/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    repeated = asp.atoms(model, "repeated_warning")
    if not repeated:
        print("MISMATCH: ASP twin lost the repeated lava warning.")
        return 1
    safe = asp.atoms(model, "safe")
    if ("rabbit", "stream") not in safe:
        print("MISMATCH: ASP twin did not reach the expected safety state.")
        return 1

    params = StoryParams("Luna", "Milo", "Pip", variation=0)
    sample = generate(params)
    required = ("lava", "stream", "together")
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story lacks required world consequences.")
        return 1
    print("OK: Python and ASP both model a repeated lava warning leading to safety.")
    return 0


CURATED = [
    StoryParams("Luna", "Milo", "Pip", variation=0, seed=11),
    StoryParams("Clover", "Nori", "Wren", variation=1, seed=22),
    StoryParams("Tess", "Bram", "Milo", variation=2, seed=33),
    StoryParams("Luna", "Clover", "Pip", variation=3, seed=44),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show repeated_warning/1.\n#show safe/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
            samples.append(generate(params))

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show repeated_warning/1.\n#show safe/2."))
        print(json.dumps({"atoms": [str(symbol) for symbol in model]}, indent=2))
        return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        print(sample.story)
        if args.trace and sample.world is not None:
            print()
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
