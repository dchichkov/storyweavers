#!/usr/bin/env python3
"""
A gentle ghost mystery about an immune little lantern, a surprising change,
and the child who learns that not every strange glow is a haunting.
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    ghost: Item
    lantern: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    ghost_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Mina", "Ollie", "Tess", "Pip", "Nico", "Ada", "Jun"]
GHOSTS = ["Wisp", "Murmur", "Boo", "Pale Poppy", "Whisper"]
PLACES = [
    "the old lighthouse",
    "the moonlit attic",
    "the quiet train station",
    "the abandoned garden",
    "the little hill house",
]


ASP_RULES = r"""
#show immune/1.
#show mystery/1.
#show transformed/1.

immune(L) :- protected(L).
mystery(L) :- glowing(L), immune(L).
transformed(L) :- mystery(L), opened(L).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("protected", "lantern"),
            asp.fact("glowing", "lantern"),
            asp.fact("opened", "lantern"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _symbol_value(symbol):
    if symbol.type.name == "Number":
        return symbol.number
    if symbol.type.name == "String":
        return symbol.string
    return symbol.name


def asp_verify() -> int:
    import asp

    shown = "#show immune/1.\n#show mystery/1.\n#show transformed/1."
    model = asp.one_model(asp_program(shown))
    actual = {
        (atom.name, tuple(_symbol_value(arg) for arg in atom.arguments))
        for atom in model
        if atom.name in {"immune", "mystery", "transformed"}
    }
    expected = {
        ("immune", ("lantern",)),
        ("mystery", ("lantern",)),
        ("transformed", ("lantern",)),
    }
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A child-friendly ghost mystery about an immune lantern."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--ghost-name", choices=GHOSTS)
    parser.add_argument("--place", choices=PLACES)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        ghost_name=args.ghost_name or rng.choice(GHOSTS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.ghost_name:
        raise StoryError("The living child and the ghost must have different names.")
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"young {params.name}",
        kind="character",
        memes={"curiosity": 0.9, "courage": 0.5},
    )
    ghost = Item(
        id="ghost",
        label=params.ghost_name,
        phrase=f"the ghost called {params.ghost_name}",
        kind="character",
        memes={"loneliness": 0.8, "hope": 0.4},
    )
    lantern = Item(
        id="lantern",
        label="lantern",
        phrase="a small blue lantern with a stubborn golden flame",
        owner="ghost",
        meters={"height": 0.3, "warmth": 0.7, "brightness": 0.8},
        memes={"memory": 0.9, "secret": 0.8, "welcome": 0.2},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.ghost_name}|{params.place}")
    return World(
        hero=hero,
        ghost=ghost,
        lantern=lantern,
        place=params.place,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    discovery: str,
    cause: str,
    resolution: str,
    transformation: str,
    ending: str,
    mystery: str,
    surprise: str,
    lines: list[str],
) -> str:
    world.facts.update(
        discovery=discovery,
        cause=cause,
        resolution=resolution,
        transformation=transformation,
        ending=ending,
        mystery=mystery,
        surprise=surprise,
        immune=True,
        transformed=True,
    )
    return " ".join(lines)


def _moon_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    g = world.ghost.label
    p = world.place
    window = _choice(
        rng,
        ["a round attic window", "a cracked tower window", "the kitchen window"],
    )
    sound = _choice(rng, ["three soft knocks", "a spoon tapping glass", "a hollow hum"])
    discovery = "the lantern's flame stayed bright even when every ordinary light went out"
    cause = "the lantern was immune to the cold ghost-wind because its flame was fed by a memory of welcome"
    transformation = "the ghost changed from a frightening shadow into a clear, smiling child"
    ending = "the lantern shone on the sill while two shadows, one warm and one pale, waved together"
    mystery = f"why the blue lantern kept glowing after {sound}"
    surprise = "the ghost was not haunting the house to frighten anyone; the ghost was guarding the lantern"
    lines = [
        f"At {p}, {h} heard {sound} behind {window}.",
        f"When {h} looked up, {g} drifted through the room with a blue lantern clasped in pale hands.",
        f'"Are you haunting this place?" asked {h}.',
        f'"I am trying to," whispered {g}, "but the lantern keeps making me feel brave."',
        f"The child had a mystery to solve: {mystery}.",
        f"{h} carried a candle near the lantern. The candle shivered and went out. A fireplace spark dimmed too. Yet the little blue flame stood straight and bright.",
        f'"Why does the cold not hurt it?" {h} asked.',
        f'"Because someone once lit it for a lonely child," said {g}. "That welcome is still inside."',
        f"Then {h} opened the lantern's tiny door. Instead of smoke, a warm golden moth flew out and settled on the ghost's shoulder.",
        f"The surprise made {g} gasp. The pale face filled with color, and {transformation}.",
        f"{h} and {g} carried the lantern through the dark rooms, where every cold corner became a place to sit and talk.",
        f"By morning, {ending}. The mystery had become a welcome.",
    ]
    return _record(
        world,
        discovery=discovery,
        cause=cause,
        resolution=f"{h} opened the lantern and released the warm memory hidden inside it",
        transformation=transformation,
        ending=ending,
        mystery=mystery,
        surprise=surprise,
        lines=lines,
    )


def _garden_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    g = world.ghost.label
    p = world.place
    flower = _choice(rng, ["a silver lily", "a night rose", "a bell-shaped flower"])
    discovery = f"the lantern's flame could not be blown out beside {flower}"
    cause = "the lantern was immune to the ghost's chilly breath because it held the last spark from a living gardener"
    transformation = "the ghost changed from a smoky figure into a gardener with muddy shoes"
    ending = "the once-silent garden glowed with lanterns, and the ghost's footprints became real prints in the soil"
    mystery = "who kept lighting the garden path after midnight"
    surprise = "the ghost had been trying to help sleeping seeds find their way upward"
    lines = [
        f"Each midnight at {p}, a trail of blue light appeared beside {flower}.",
        f"{h} followed it and found {g} bending over the garden with the small blue lantern.",
        f'"Do ghosts grow flowers?" asked {h}.',
        f'"Only the ones who remember how," said {g}. "But this garden forgets me every morning."',
        f"The mystery was {mystery}.",
        f"{h} watched {g} breathe a cold silver breath across the lantern. The flame leaned, flickered, and sprang back brighter than before.",
        f'"It is immune to your ghost-wind," said {h}.',
        f'"No," said {g}. "It is carrying someone else\'s warm breath."',
        f"Together they opened the lantern. A tiny seed, glowing like a star, rolled into the soil.",
        f"At once, {flower} unfolded, and {transformation}.",
        f"The new gardener laughed and planted rows of sleepy seeds while {h} held the lantern high.",
        f"At dawn, {ending}. The garden no longer needed a ghost to remember it.",
    ]
    return _record(
        world,
        discovery=discovery,
        cause=cause,
        resolution=f"{h} helped open the lantern so its warm seed could return to the garden",
        transformation=transformation,
        ending=ending,
        mystery=mystery,
        surprise=surprise,
        lines=lines,
    )


def _station_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    g = world.ghost.label
    p = world.place
    train = _choice(rng, ["the midnight train", "the blue mail train", "the little morning train"])
    discovery = f"the lantern always brightened before {train} arrived"
    cause = "the lantern was immune to the station's rattling darkness because it remembered a promise to guide one traveler home"
    transformation = "the ghost changed from a wandering blur into a solid conductor"
    ending = "the lantern hung above the station door, and the former ghost waved passengers safely toward home"
    mystery = "why the empty platform received a blue signal"
    surprise = "the ghost had not missed a train; the ghost had been waiting for a lost promise"
    lines = [
        f"At {p}, {h} saw a blue lantern glow on an empty platform before {train}.",
        f"Beside it floated {g}, whose feet never touched the boards.",
        f'"Who are you signaling?" asked {h}.',
        f'"Someone who promised to come back," said {g}. "I have waited so long that I forgot the name."',
        f"{h} had a mystery to solve: {mystery}.",
        f"The station bell rang, and a gust rushed through the waiting room. Papers flew. Dust spun. The lantern did not go out.",
        f'"Your lantern is immune to the wind," said {h}.',
        f'"It is not brave," replied {g}. "It is remembering for me."',
        f"{h} opened the lantern and found a little brass ticket inside. On it was written one word: HOME.",
        f"The surprise made {g} sit down. Then {transformation}.",
        f"Together they placed the ticket beneath the station clock, where travelers could read it.",
        f"After that, {ending}. The promise finally had a direction.",
    ]
    return _record(
        world,
        discovery=discovery,
        cause=world.lantern.phrase + " held a promise that kept its flame alive against the station wind",
        resolution=f"{h} found the brass HOME ticket inside the lantern and placed it beneath the clock",
        transformation=transformation,
        ending=ending,
        mystery=mystery,
        surprise=surprise,
        lines=lines,
    )


def _attic_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    g = world.ghost.label
    p = world.place
    object_name = _choice(rng, ["a toy boat", "a red ribbon", "a wooden music box"])
    discovery = f"the lantern's light revealed {object_name} hidden inside a wall"
    cause = "the lantern was immune to the attic's dusty darkness because it was made to reveal things that had been forgotten"
    transformation = "the ghost changed from a frightening outline into a small, cheerful keeper of lost things"
    ending = "the lantern lit a shelf of returned treasures, and the attic felt like a room instead of a secret"
    mystery = "what made tiny footsteps cross the ceiling every night"
    surprise = "the footsteps belonged to lost memories looking for their owners"
    lines = [
        f"In the attic of {p}, {h} heard tiny footsteps crossing the ceiling.",
        f"{g} appeared beside an old trunk, holding the blue lantern close.",
        f'"Are you the one making those steps?" asked {h}.',
        f'"No," said {g}. "I am the one trying to find what they lost."',
        f"The mystery was {mystery}.",
        f"{h} raised the lantern. Its flame shone through cobwebs, dust, and darkness without shrinking.",
        f'"It is immune to this gloom," said {h}.',
        f'"It knows that forgotten things still matter," whispered {g}.',
        f"The light touched a loose board. Behind it lay {object_name}, along with a row of small objects wrapped in paper.",
        f"Then the surprise arrived: the footsteps were not made by feet at all. They were the soft sounds of memories knocking from inside the walls.",
        f"When {h} unwrapped the first bundle, {transformation}.",
        f"Together they carried each treasure downstairs and asked the neighbors who had lost it.",
        f"By sunrise, {ending}. The attic's mystery had become a cupboard of kindness.",
    ]
    return _record(
        world,
        discovery=discovery,
        cause=world.lantern.phrase + " was made to reveal forgotten things and could not be dimmed by dust",
        resolution=f"{h} used the lantern to reveal the hidden shelf and returned the wrapped treasures",
        transformation=transformation,
        ending=ending,
        mystery=mystery,
        surprise=surprise,
        lines=lines,
    )


def _hill_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    g = world.ghost.label
    p = world.place
    sound = _choice(rng, ["a bell", "a flute", "a sleepy drum"])
    discovery = f"the lantern made no shadow when {sound} played"
    cause = "the lantern was immune to the hill's ghostly gloom because it was filled with a living person's first laugh"
    transformation = "the ghost changed from a chilly shape into a warm companion with a bright laugh"
    ending = "the lantern cast two happy shadows down the hill, one small and one newly real"
    mystery = "why the hill had one extra shadow under the moon"
    surprise = "the shadow belonged to a laugh that had been waiting for its owner"
    lines = [
        f"On the hill above {p}, {h} noticed one extra shadow beneath the moon.",
        f"At its center stood {g}, holding the blue lantern while {sound} sounded far below.",
        f'"Is that your shadow?" asked {h}.',
        f'"I do not think ghosts are supposed to have one," said {g}.',
        f"The mystery was {mystery}.",
        f"{h} waved a hand before the lantern. The hand made a shadow. A cloud passed over the moon. The lantern stayed golden and bright.",
        f'"The darkness cannot swallow it," said {h}.',
        f'"Perhaps it is carrying something darkness cannot eat," said {g}.',
        f"They opened the lantern and heard a baby's first laugh, small as a silver pebble.",
        f"The sound flew into the ghost, and {transformation}.",
        f"{h} laughed too, and the lantern answered with a warm golden glow.",
        f"Before they walked home, {ending}. The extra shadow had become a friend.",
    ]
    return _record(
        world,
        discovery=discovery,
        cause="the lantern held a living first laugh, which gave its flame a warmth the hill's gloom could not swallow",
        resolution=f"{h} helped open the lantern and let the stored laugh return to the ghost",
        transformation=transformation,
        ending=ending,
        mystery=mystery,
        surprise=surprise,
        lines=lines,
    )


ARC_BUILDERS = [_moon_arc, _garden_arc, _station_arc, _attic_arc, _hill_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x4C554E41)
    return ARC_BUILDERS[world.seed % len(ARC_BUILDERS)](world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    facts = world.facts
    return [
        QAItem(
            question=f"What mystery did {h} try to solve?",
            answer=f"{h} tried to solve {facts['mystery']}.",
        ),
        QAItem(
            question="What surprising truth did the characters discover?",
            answer=f"The surprising truth was that {facts['surprise']}.",
        ),
        QAItem(
            question=f"How did {h} help solve the mystery?",
            answer=f"{facts['resolution']}.",
        ),
        QAItem(
            question="How did the ghost change?",
            answer=f"The ghost transformed when {facts['transformation']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does immune mean?",
            answer="Immune means protected from being harmed or changed by something that usually causes harm.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to understand by noticing clues and asking questions.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about a spirit or strange haunting, often with a mystery, a frightening moment, or a surprising explanation.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means a major change in appearance, condition, or behavior.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle ghost story for young children about an immune lantern.",
        f"Create a mystery to solve at {world.place}, where a ghost and a child discover a surprising transformation.",
        "Tell a child-friendly ghost story with a clear clue, a surprise, and a warm ending.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.ghost, world.lantern]:
        lines.append(
            f"  {entity.id:7} {entity.kind:9} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    output = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        output.append(f"{index}. {prompt}")
    output.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    output.extend(["", "== World QA =="])
    for item in sample.world_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    return "\n".join(output)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show immune/1.\n#show mystery/1.\n#show transformed/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "3 compatible logical atoms: immune(lantern), "
            "mystery(lantern), transformed(lantern)"
        )
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Luna",
                ghost_name="Wisp",
                place="the old lighthouse",
                seed=101,
            ),
            StoryParams(
                name="Mina",
                ghost_name="Murmur",
                place="the moonlit attic",
                seed=102,
            ),
            StoryParams(
                name="Ollie",
                ghost_name="Boo",
                place="the quiet train station",
                seed=103,
            ),
            StoryParams(
                name="Tess",
                ghost_name="Pale Poppy",
                place="the abandoned garden",
                seed=104,
            ),
            StoryParams(
                name="Pip",
                ghost_name="Whisper",
                place="the little hill house",
                seed=105,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + attempt))
            params.seed = base_seed + attempt
            sample = generate(params)
            attempt += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not create the requested number of distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
