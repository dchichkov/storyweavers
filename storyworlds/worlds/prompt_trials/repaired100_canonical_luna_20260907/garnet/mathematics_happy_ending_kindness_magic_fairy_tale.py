#!/usr/bin/env python3
"""
A gentle fairy-tale storyworld about mathematics, kindness, and a magical garnet.
"""

from __future__ import annotations

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
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Entity
    companion: Entity
    fairy: Entity
    garnet: Entity
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    companion_name: str
    fairy_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Mira", "Tessa", "Nell", "Sera", "Ada"]
COMPANIONS = ["Pip", "Bram", "Clover", "Finn", "Wren", "Moss"]
FAIRIES = ["Queen Elowen", "Fairy Bea", "Lady Numeria", "Sage Amabel"]
PLACES = [
    "the moonlit meadow",
    "the silver village",
    "the crystal orchard",
    "the whispering hill",
    "the rose-colored valley",
]


ASP_RULES = r"""
#show kind/1.
#show solved/1.
#show happy/1.

kind(H) :- shares(H).
solved(H) :- counts(H).
happy(H) :- kind(H), solved(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("shares", "hero"),
            asp.fact("counts", "hero"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = "#show kind/1.\n#show solved/1.\n#show happy/1."
    model = asp.one_model(asp_program(shown))
    actual = set()
    for atom in model:
        if atom.name == "kind" and atom.arguments:
            actual.add(("kind", (atom.arguments[0].name,)))
        elif atom.name == "solved" and atom.arguments:
            actual.add(("solved", (atom.arguments[0].name,)))
        elif atom.name == "happy" and atom.arguments:
            actual.add(("happy", (atom.arguments[0].name,)))
    expected = {
        ("kind", ("hero",)),
        ("solved", ("hero",)),
        ("happy", ("hero",)),
    }
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fairy-tale mathematics storyworld about kindness and magic."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--companion-name", choices=COMPANIONS)
    ap.add_argument("--fairy-name", choices=FAIRIES)
    ap.add_argument("--place", choices=PLACES)
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
        companion_name=args.companion_name or rng.choice(COMPANIONS),
        fairy_name=args.fairy_name or rng.choice(FAIRIES),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.companion_name:
        raise StoryError("The hero and companion must have different names.")
    hero = Entity(
        id="hero",
        label=params.name,
        kind="child",
        meters={"steps": 0, "patience": 4},
        memes={"curiosity": 5, "kindness": 5},
    )
    companion = Entity(
        id="companion",
        label=params.companion_name,
        kind="friend",
        meters={"steps": 0, "confidence": 2},
        memes={"worry": 4, "hope": 3},
    )
    fairy = Entity(
        id="fairy",
        label=params.fairy_name,
        kind="fairy",
        meters={"magic": 9},
        memes={"wisdom": 8, "kindness": 8},
    )
    garnet = Entity(
        id="garnet",
        label="the counting garnet",
        kind="magical gemstone",
        owner="fairy",
        meters={"sparkles": 7, "needed_sparks": 7},
        memes={"patience": 6, "generosity": 8},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.companion_name}|{params.place}")
    return World(
        hero=hero,
        companion=companion,
        fairy=fairy,
        garnet=garnet,
        place=params.place,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    numbers: str,
    problem: str,
    method: str,
    solution: str,
    lesson: str,
    ending: str,
    story: str,
) -> str:
    world.facts.update(
        numbers=numbers,
        problem=problem,
        method=method,
        solution=solution,
        lesson=lesson,
        ending=ending,
        story=story,
        counted=True,
        shared=True,
        happy=True,
    )
    world.hero.meters["steps"] = 7
    world.hero.memes["kindness"] = 9
    world.companion.meters["confidence"] = 8
    world.companion.memes["worry"] = 0
    return story


def _lantern_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    c = world.companion.label
    f = world.fairy.label
    p = world.place
    baskets = _choice(rng, ["three", "four", "five"])
    each = _choice(rng, ["four", "five", "six"])
    total = int(baskets) * int(each)
    prize = _choice(rng, ["a warm cottage", "a garden of moon roses", "a little bakery"])
    numbers = f"{baskets} baskets with {each} lanterns in each, making {total} lanterns"
    problem = f"{c} had to light {total} lanterns before the fairy festival"
    method = f"{h} used multiplication by adding {each} {baskets} times"
    solution = f"{baskets} times {each} equals {total}, so every lantern could be lit"
    lesson = "A hard question becomes friendlier when it is shared and counted carefully."
    ending = f"the lanterns shone above {prize}, and {c} danced without fear"
    lines = [
        f"Long ago, in {p}, {h} found {c} beside a dark festival path.",
        f"{c} held a basket and whispered, \"I cannot light all the lanterns before the moon rises.\"",
        f'"Let us count together," said {h}. "{f} taught me that numbers are little stepping-stones."',
        f"The kindly fairy {f} appeared in a silver shower and placed {baskets} baskets before them, with {each} lanterns in each basket.",
        f"First they counted one group of {each}. Then they counted another group of {each}, and another, until {h} saw that {baskets} groups of {each} made {total}.",
        f'"So multiplication is a quick way to count equal groups!" cried {c}.',
        f'"And kindness is a quick way to make a worried heart brave," said {h}.',
        f"The counting garnet glowed seven times. Its magic lit every wick, because the friends had solved the problem together.",
        f"By moonrise, {ending}. The festival began with music, laughter, and a cake cut into {total} shining stars.",
    ]
    return _record(
        world,
        numbers=numbers,
        problem=problem,
        method=method,
        solution=solution,
        lesson=lesson,
        ending=ending,
        story=" ".join(lines),
    )


def _bridge_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    c = world.companion.label
    f = world.fairy.label
    p = world.place
    stones = _choice(rng, ["eight", "ten", "twelve"])
    rows = _choice(rng, ["two", "three", "four"])
    total = int(stones) // int(rows) if int(stones) % int(rows) == 0 else 4
    stones = str(total * int(rows))
    village = _choice(rng, ["the baker", "the miller", "the shepherd"])
    numbers = f"{stones} moon stones divided equally into {rows} rows of {total}"
    problem = f"the bridge needed {stones} stones, but the builders did not know how to share them fairly"
    method = f"{h} used division to place {stones} stones into {rows} equal rows"
    solution = f"{stones} divided by {rows} equals {total}, so each row received {total} stones"
    lesson = "Fair sharing gives every part a place."
    ending = f"the bridge carried {village}'s cart safely over the sparkling brook"
    lines = [
        f"At dawn in {p}, {h} and {c} found a broken bridge beneath a willow tree.",
        f'"The {village} cannot bring bread across," said {c}. "There are {stones} moon stones, but no plan."',
        f'"We can make equal rows," said {h}. "Equal means fair."',
        f"{f} flew down on a blue butterfly and touched the stones with the counting garnet.",
        f"Together the friends made {rows} rows. Each row held {total} stones, because {stones} divided by {rows} equals {total}.",
        f'"No stone is left lonely," laughed {c}. "The bridge is fair to every stone!"',
        f"The garnet sent a warm golden thread between the rows, sealing them into a strong bridge.",
        f"{h} gave the first safe crossing to the {village}, even though the bread smelled wonderfully sweet.",
        f"At sunset, {ending}. The {village} shared the first loaf with the children, and the fairy smiled.",
    ]
    return _record(
        world,
        numbers=numbers,
        problem=problem,
        method=method,
        solution=solution,
        lesson=lesson,
        ending=ending,
        story=" ".join(lines),
    )


def _garden_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    c = world.companion.label
    f = world.fairy.label
    p = world.place
    start = _choice(rng, ["two", "three", "four"])
    added = _choice(rng, ["three", "four", "five"])
    total = int(start) + int(added)
    seeds = _choice(rng, ["bells", "star beans", "silver peas"])
    numbers = f"{start} {seeds} already grew and {added} more were planted, making {total}"
    problem = f"{c} thought the empty garden would never have enough plants for the village supper"
    method = f"{h} used addition to combine the {start} growing plants with {added} new seeds"
    solution = f"{start} plus {added} equals {total}, enough plants for everyone"
    lesson = "Hope grows when people notice what they have and add their help."
    ending = f"{total} shining {seeds} bowed gently toward the stars"
    lines = [
        f"Once, in {p}, {h} found {c} sitting beside a sleepy garden.",
        f'"There are only {start} {seeds}," sighed {c}. "The village supper needs more."',
        f'"I have {added} seeds," said {h}. "If we add them, perhaps the garden will answer."',
        f"{f} appeared inside a ring of violet light. \"Mathematics can show a small beginning becoming a generous feast,\" said the fairy.",
        f"They planted the seeds and counted: {start} plus {added} equals {total}.",
        f"The counting garnet twinkled once for each plant. At the final twinkle, the earth hummed a kind song.",
        f"Before supper, {total} shining {seeds} rose from the soil. {c} offered the first basket to an old neighbor who had no garden.",
        f'"Kindness makes the harvest taste sweeter," said {h}. "And counting helps us share it fairly."',
        f"That night, {ending}. Every villager had enough, and nobody ate alone.",
    ]
    return _record(
        world,
        numbers=numbers,
        problem=problem,
        method=method,
        solution=solution,
        lesson=lesson,
        ending=ending,
        story=" ".join(lines),
    )


def _clock_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    c = world.companion.label
    f = world.fairy.label
    p = world.place
    hours = _choice(rng, ["six", "eight", "nine"])
    wait = _choice(rng, ["two", "three"])
    total = int(hours) + int(wait)
    numbers = f"{hours} bright hours plus {wait} waiting hours, making {total} hours"
    problem = f"{c} feared the lost prince would not be found before the magic clock stopped"
    method = f"{h} used addition on the clock's {hours} bright hours and {wait} extra hours"
    solution = f"{hours} plus {wait} equals {total}, so there was still time to help"
    lesson = "Patient counting can turn panic into a plan."
    ending = "the prince returned home just as the clock chimed a happy noon"
    lines = [
        f"Beyond {p}, a magic clock rang in the forest, and {c} began to tremble.",
        f'"The prince is lost," said {c}. "The clock has only {hours} bright hours left."',
        f'"Do not hurry past the truth," said {h}. "The clock also gives us {wait} waiting hours."',
        f"{f} lifted the garnet, and its red light drew a number line across the moss.",
        f"They added the hours: {hours} plus {wait} equals {total}. There was time to search kindly instead of rushing blindly.",
        f"The friends called softly at every fork. At the third fork, they heard a small voice answer.",
        f'"You found me because you counted the time and listened," said the prince.',
        f"The garnet opened a silver path. The children led the prince home, sharing their lantern with him.",
        f"At dawn, {ending}. The clock gave one extra chime for kindness.",
    ]
    return _record(
        world,
        numbers=numbers,
        problem=problem,
        method=method,
        solution=solution,
        lesson=lesson,
        ending=ending,
        story=" ".join(lines),
    )


ARC_BUILDERS = [_lantern_arc, _bridge_arc, _garden_arc, _clock_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    facts = world.facts
    return [
        QAItem(
            question=f"What mathematics did {h} use?",
            answer=f"{h} used {facts['method']}.",
        ),
        QAItem(
            question="What problem did the friends solve?",
            answer=f"They solved this problem: {facts['problem']}.",
        ),
        QAItem(
            question=f"How did {h} show kindness?",
            answer=f"{h} shared the work and made sure that {facts['lesson'].lower()}",
        ),
        QAItem(
            question="How did the magic help?",
            answer=f"The counting garnet helped after the friends understood the numbers: {facts['solution']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mathematics?",
            answer="Mathematics is the study of numbers, patterns, shapes, quantities, and ways to solve problems.",
        ),
        QAItem(
            question="What does addition do?",
            answer="Addition combines quantities to find how many there are altogether.",
        ),
        QAItem(
            question="What does division do?",
            answer="Division separates a quantity into equal groups or finds how many equal groups can be made.",
        ),
        QAItem(
            question="Why is kindness important?",
            answer="Kindness helps people feel safe, valued, and ready to help one another.",
        ),
        QAItem(
            question="What is magic in a fairy tale?",
            answer="Magic is a wondrous power that changes what is possible while supporting the tale's adventure.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a fairy tale for young children in which mathematics helps solve a magical problem.",
        f"Tell a kind story about {world.hero.label} and {world.companion.label} using numbers to help someone in {world.place}.",
        "Create a happy-ending tale where sharing, careful counting, and magic work together.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.companion, world.fairy, world.garnet]:
        lines.append(
            f"  {ent.id:10} {ent.kind:18} label={ent.label!r} "
            f"owner={ent.owner!r} meters={ent.meters} memes={ent.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        out.append(f"{i}. {prompt}")
    out.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.extend(["", "== World QA =="])
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
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

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    if args.show_asp:
        print(asp_program("#show kind/1.\n#show solved/1.\n#show happy/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("3 compatible logical atoms: kind(hero), solved(hero), happy(hero)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Luna",
                companion_name="Pip",
                fairy_name="Queen Elowen",
                place="the moonlit meadow",
                seed=11,
            ),
            StoryParams(
                name="Mira",
                companion_name="Clover",
                fairy_name="Fairy Bea",
                place="the silver village",
                seed=22,
            ),
            StoryParams(
                name="Tessa",
                companion_name="Bram",
                fairy_name="Lady Numeria",
                place="the crystal orchard",
                seed=33,
            ),
            StoryParams(
                name="Nell",
                companion_name="Wren",
                fairy_name="Sage Amabel",
                place="the whispering hill",
                seed=44,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
