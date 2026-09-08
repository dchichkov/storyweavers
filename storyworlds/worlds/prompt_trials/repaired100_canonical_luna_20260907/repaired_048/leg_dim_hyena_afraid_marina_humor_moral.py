#!/usr/bin/env python3
"""
A gentle animal storyworld set in a marina.

A leg-dim hyena feels afraid when a floating bell goes silent. Humor, kindness,
and a moral choice help the animals repair the trouble together.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    place: str
    hyena: str
    helper: str
    boat: str
    bell: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trouble:
    object_name: str
    clue: str
    false_guess: str
    test: str
    cause: str
    repair: str
    joke: str
    moral: str
    ending: str


TROUBLES = [
    Trouble(
        "a striped mooring rope",
        "wet blue fibers curled around the bell's small hammer",
        "a grumpy seal hiding under the dock",
        "lifted the rope with a boat hook and watched the hammer swing freely",
        "the rope had wrapped around the hammer when the tide pulled the boat sideways",
        "moved the rope to a high peg and tied a bright marker on it",
        "the hyena tried to look brave, but his knees knocked like two tiny oars",
        "Kindness begins when we help someone who is afraid instead of laughing at them.",
        "the repaired bell rang above calm water while the hyena laughed at his own wobbly knees",
    ),
    Trouble(
        "a basket of shiny fish scales",
        "one silver scale rested inside the bell housing",
        "a pelican who wanted the bell for a hat",
        "placed the basket farther away and gently shook one scale beside the bell",
        "a gust had blown the light basket against the bell and jammed its clapper",
        "latched the basket under a bench and cleaned the clapper",
        "the hyena wore the basket on his head and announced himself as Captain Sparkle",
        "A silly mistake deserves a patient fix, not a cruel accusation.",
        "Captain Sparkle bowed beneath the ringing bell as the pelican applauded",
    ),
    Trouble(
        "a loose yellow pennant",
        "its torn corner was caught on the bell's cord",
        "a pirate crab sneaking along the pier",
        "pulled the pennant back inch by inch while everyone watched the cord",
        "the wind had twisted the pennant around the cord and stopped the bell",
        "stitched the pennant and clipped it below the cord",
        "the hyena whispered to the pennant, and the pennant gave no answer because it had no ears",
        "Good helpers check the facts before blaming a friend.",
        "the yellow pennant fluttered safely as the bell welcomed every boat",
    ),
    Trouble(
        "a floating orange life ring",
        "a fresh scrape on the ring matched the bell's wooden frame",
        "a shark practicing a surprise visit",
        "guided the ring away from the dock and listened for the bell to move",
        "the tide had pushed the ring into the bell again and again",
        "fastened the life ring to a short line where it could help without bumping anything",
        "Caring for safety can solve a problem before fear grows larger.",
        "the life ring bobbed proudly beside the dock while the bell rang in the sun",
    ),
]


OPENINGS = [
    "Morning painted the marina gold.",
    "At the marina, boats bobbed like sleepy ducks.",
    "The marina was busy with gulls, ropes, and gentle waves.",
    "Near the first fishing boats, the day began with a curious silence.",
]

JOKES = [
    '"I am not afraid," said the hyena, while hiding behind a bucket.',
    '"My brave face is still drying," the hyena admitted.',
    '"I meant to wobble," said the hyena. "It is a very advanced dance."',
    '"If the trouble is a monster, I will politely ask it to leave," said the hyena.',
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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


def check_world(world: World) -> None:
    hyena = world.entities["hyena"]
    bell = world.entities["bell"]
    if hyena.meters.get("leg_dim", 0) >= THRESHOLD:
        hyena.memes["afraid"] = 1
        world.fired.add(("hyena_afraid",))
    if bell.meters.get("ringing", 0) < THRESHOLD:
        world.fired.add(("bell_silent",))


def resolve_world(world: World) -> None:
    hyena = world.entities["hyena"]
    bell = world.entities["bell"]
    hyena.memes["afraid"] = 0
    hyena.memes["relief"] = 1
    hyena.memes["kindness"] = 1
    bell.meters["ringing"] = 1
    world.fired.add(("kindness_used",))
    world.fired.add(("bell_repaired",))


def tell(world: World, params: StoryParams) -> World:
    seed = params.seed
    if seed is None:
        seed = sum((i + 1) * ord(c) for i, c in enumerate("|".join(vars(params).values().__str__())))
    rng = random.Random(seed ^ 0x48A9)

    trouble = rng.choice(TROUBLES)
    opening = rng.choice(OPENINGS)
    joke = rng.choice(JOKES)

    hyena = world.add(Entity("hyena", "character", "hyena", params.hyena))
    helper = world.add(Entity("helper", "character", "otter", params.helper))
    boat = world.add(Entity("boat", "thing", "boat", params.boat))
    bell = world.add(Entity("bell", "thing", "bell", params.bell))
    pier = world.add(Entity("marina", "place", "marina", "marina"))

    hyena.meters["leg_dim"] = 1
    hyena.memes["kindness"] = 0
    hyena.memes["afraid"] = 0
    bell.meters["ringing"] = 0
    check_world(world)

    world.say(opening)
    world.say(
        f"{hyena.label} the hyena lived beside the marina with {helper.label} the otter."
    )
    world.say(
        f"{hyena.label} had one leg-dim step that made him wobble, but {helper.label} always walked beside him."
    )
    world.say(
        f"Their favorite boat was {boat.label}, and its little {bell.label} guided boats safely to the dock."
    )

    world.para()
    world.say(f"That morning, the {bell.label} was silent, and {hyena.label} felt afraid.")
    world.say(f"Nearby, {trouble.object_name} lay beside the dock.")
    world.say(joke)
    world.say(f'"I hear your worry," said {helper.label}. "We can look carefully together."')

    world.para()
    world.say(
        f"They found a clue: {trouble.clue}."
    )
    world.say(
        f"{hyena.label} guessed it might be {trouble.false_guess}, but {helper.label} shook his head kindly."
    )
    world.say(f'"Let us test the clue before we blame anyone," said {helper.label}.')
    world.say(f"They {trouble.test}.")
    world.say(f"The test showed that {trouble.cause}.")
    world.say(
        f"{hyena.label} stopped hiding behind the bucket. " + trouble.joke.capitalize() + "."
    )

    resolve_world(world)
    world.para()
    world.say(f"Together, the friends {trouble.repair}.")
    world.say(
        f"The {bell.label} rang again, and {hyena.label} took one careful step, then another."
    )
    world.say(f'"Thank you for helping me," said {hyena.label}.')
    world.say(f'"Bravery can borrow a paw," replied {helper.label}.')
    world.say(f"{trouble.moral}")
    world.say(f"By noon, {trouble.ending}.")

    world.facts.update(
        hyena=hyena,
        helper=helper,
        boat=boat,
        bell=bell,
        place="marina",
        trouble=trouble,
        clue=trouble.clue,
        false_guess=trouble.false_guess,
        cause=trouble.cause,
        repair=trouble.repair,
        moral=trouble.moral,
        ending=trouble.ending,
    )
    return world


PLACES = {"marina": Setting("marina")}
HYENA_NAMES = ["Marnie", "Hugo", "Ziggy", "Nell"]
HELPER_NAMES = ["Milo", "Pip", "Tula", "Bram"]
BOATS = ["Blue Minnow", "Sunny Shell", "Little Wave", "Red Canoe"]
BELLS = ["brass bell", "harbor bell", "little bell", "blue bell"]


ASP_RULES = r"""
afraid(H) :- hyena(H), leg_dim(H), silent(B), bell(B).
helped(H) :- afraid(H), kindness(H), repaired(B).
safe(H) :- helped(H).

#show afraid/1.
#show helped/1.
#show safe/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    lines.extend(
        [
            asp.fact("hyena", "hyena"),
            asp.fact("leg_dim", "hyena"),
            asp.fact("silent", "bell"),
            asp.fact("bell", "bell"),
            asp.fact("kindness", "hyena"),
            asp.fact("repaired", "bell"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animal storyworld about a leg-dim hyena at a marina.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hyena")
    parser.add_argument("--helper")
    parser.add_argument("--boat")
    parser.add_argument("--bell")
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
    return StoryParams(
        place=args.place or "marina",
        hyena=args.hyena or rng.choice(HYENA_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        boat=args.boat or rng.choice(BOATS),
        bell=args.bell or rng.choice(BELLS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle Animal Story using the words "leg-dim", "hyena", and "afraid".',
        f"Tell a humorous marina story in which {f['hyena'].label} receives kindness from {f['helper'].label}.",
        f"Write a child-facing moral tale explaining how {f['clue']} led to the repair.",
    ]


def story_questions(world: World) -> list[QAItem]:
    f = world.facts
    h = f["hyena"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Why was {h.label} afraid at the marina?",
            answer=f"{h.label} was afraid because the {f['bell'].label} was silent and the trouble near it seemed mysterious.",
        ),
        QAItem(
            question=f"What clue did {h.label} and {helper.label} find?",
            answer=f"They found that {f['clue']}.",
        ),
        QAItem(
            question="What caused the bell to stop ringing?",
            answer=f"They discovered that {f['cause']}.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"Together, they {f['repair']}.",
        ),
        QAItem(
            question="What moral value did the story show?",
            answer=f"It showed kindness because the friends helped the afraid hyena instead of blaming or mocking him. {f['moral']}",
        ),
    ]


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marina?",
            answer="A marina is a place beside water where boats can be kept and cared for.",
        ),
        QAItem(
            question="What is a hyena?",
            answer="A hyena is a wild mammal known for strong jaws and a distinctive call that can sound like laughter.",
        ),
        QAItem(
            question="Why is kindness useful when someone is afraid?",
            answer="Kindness helps a frightened friend feel safe enough to think, ask questions, and try a solution.",
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
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={dict(entity.meters)} memes={dict(entity.memes)}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if not params.hyena or not params.helper:
        raise StoryError("A hyena and a helper are required.")
    world = World(PLACES[params.place])
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show afraid/1.\n#show helped/1.\n#show safe/1."))
    afraid = set(asp.atoms(model, "afraid"))
    helped = set(asp.atoms(model, "helped"))
    safe = set(asp.atoms(model, "safe"))
    if afraid == {("hyena",)} and helped == {("hyena",)} and safe == {("hyena",)}:
        sample = generate(
            StoryParams(
                place="marina",
                hyena="Marnie",
                helper="Milo",
                boat="Blue Minnow",
                bell="brass bell",
                seed=7,
            )
        )
        if "leg-dim" in sample.story and "hyena" in sample.story and "afraid" in sample.story:
            print("OK: ASP/Python parity and generated-story checks passed.")
            return 0
    print("MISMATCH: ASP/Python parity check failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show afraid/1.\n#show helped/1.\n#show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show afraid/1.\n#show helped/1.\n#show safe/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            StoryParams("marina", "Marnie", "Milo", "Blue Minnow", "brass bell", base_seed),
            StoryParams("marina", "Hugo", "Pip", "Sunny Shell", "harbor bell", base_seed + 1),
            StoryParams("marina", "Ziggy", "Tula", "Little Wave", "little bell", base_seed + 2),
            StoryParams("marina", "Nell", "Bram", "Red Canoe", "blue bell", base_seed + 3),
        ]
        samples = [generate(p) for p in presets]
    else:
        for index in range(max(1, args.n)):
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
