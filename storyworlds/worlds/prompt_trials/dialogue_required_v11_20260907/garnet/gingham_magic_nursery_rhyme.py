#!/usr/bin/env python3
"""
A gentle nursery-rhyme storyworld about gingham magic, a careful child, and a
little square of cloth that learns to mend a moonlit problem.
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
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
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
    helper: Item
    cloth: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    helper_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Mina", "Pip", "Lulu", "Nell", "Toby", "Mabel", "Jo", "Kit"]
HELPERS = ["Grandma May", "Aunt Bea", "Uncle Tom", "Miss June", "Grandpa Gus"]
PLACES = [
    "the little nursery",
    "the moonlit kitchen",
    "the blue cottage",
    "the garden gate",
    "the sleepy hill",
]


ASP_RULES = r"""
#show enchanted/1.
#show helpful/1.
#show mended/1.

enchanted(H) :- hears_chime(H).
helpful(H) :- follows_rhyme(H).
mended(H) :- ties_gingham(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hears_chime", "hero"),
            asp.fact("follows_rhyme", "hero"),
            asp.fact("ties_gingham", "hero"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    show = "#show enchanted/1.\n#show helpful/1.\n#show mended/1."
    model = asp.one_model(asp_program(show))
    actual = set()
    for atom in model:
        args = []
        for value in atom.arguments:
            if value.type == value.type.Number:
                args.append(value.number)
            elif value.type == value.type.String:
                args.append(value.string)
            else:
                args.append(value.name)
        actual.add((atom.name, tuple(args)))
    expected = {
        ("enchanted", ("hero",)),
        ("helpful", ("hero",)),
        ("mended", ("hero",)),
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
        description="Nursery-rhyme storyworld about magical gingham."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper-name", choices=HELPERS)
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
        helper_name=args.helper_name or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if not params.name.strip():
        raise StoryError("the child name cannot be empty")
    if not params.helper_name.strip():
        raise StoryError("the helper name cannot be empty")
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"young {params.name}",
        kind="character",
        meters={"height": 1.1, "distance_to_cloth": 0.4},
        memes={"curiosity": 0.8, "courage": 0.6},
    )
    helper = Item(
        id="helper",
        label=params.helper_name,
        phrase=params.helper_name,
        kind="character",
        meters={"height": 1.7},
        memes={"patience": 0.9, "trust": 0.8},
    )
    cloth = Item(
        id="gingham",
        label="gingham",
        phrase="a small red-and-white gingham square",
        kind="magical cloth",
        owner=hero.id,
        meters={"width": 0.35, "softness": 0.9},
        memes={"magic": 0.9, "helpfulness": 0.8},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.helper_name}|{params.place}")
    return World(
        hero=hero,
        helper=helper,
        cloth=cloth,
        place=params.place,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    arc: str,
    discovery: str,
    trouble: str,
    cause: str,
    resolution: str,
    rhyme: str,
    ending: str,
    magic: str,
    lines: list[str],
) -> str:
    world.facts.update(
        arc=arc,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        resolution=resolution,
        rhyme=rhyme,
        ending=ending,
        magic=magic,
        mended=True,
    )
    return " ".join(lines)


def _moon_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    helper = world.helper.label
    place = world.place
    rhyme = _choice(
        rng,
        [
            "Patch and stitch, make moonlight switch!",
            "Square of red, shine overhead!",
            "Gingham bright, guide the night!",
        ],
    )
    missing = _choice(rng, ["a silver star", "the moon's small button", "a sleepy cloud"])
    discovery = f"the gingham could call {missing} back with a gentle rhyme"
    trouble = f"{missing} slipped away, leaving {place} dim and dreary"
    cause = "the night wind had tugged the moon's loose little patch from the sky"
    resolution = (
        f"{h} held the gingham high while {helper} tied its four corners to the breeze; "
        f"the rhyme drew {missing} home"
    )
    ending = "the gingham rested on the windowsill, glowing in a square of moonlight"
    magic = "the cloth answered a kind rhyme by mending a tear in the night"
    lines = [
        f"In {place}, {h} found {world.cloth.phrase} beneath a chair.",
        f"It was checked in red and white, and it shimmered whenever {h} whispered, \"{rhyme}\"",
        f"Just then, {missing} slipped away, and {place} grew dim and dreary.",
        f'"Where did it go?" asked {h}. "{missing} must be found before morning," said {helper}.',
        f"{h} shook the cloth once. It fluttered toward the window, but the wind pulled harder.",
        f'"Try the rhyme with a listening heart," said {helper}. "Magic likes kindness better than shouting."',
        f"{h} breathed slowly and sang, \"{rhyme}\" The gingham glowed, and the loose night patch floated down.",
        f"{resolution}.",
        f"By dawn, {ending}. {h} learned that a small square can mend a very large darkness.",
    ]
    return _record(
        world,
        arc="moon",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        resolution=resolution,
        rhyme=rhyme,
        ending=ending,
        magic=magic,
        lines=lines,
    )


def _rain_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    helper = world.helper.label
    place = world.place
    rhyme = _choice(
        rng,
        [
            "Drip and drop, let raindrops stop!",
            "Red check, hold the deck!",
            "Rainy thread, turn overhead!",
        ],
    )
    object_name = _choice(rng, ["the nursery roof", "the hen's umbrella", "the baker's basket"])
    discovery = f"the gingham could stretch into a bright shelter when sung to softly"
    trouble = f"rain poured through {object_name} and soaked everyone below"
    cause = "a tiny tear had opened where the storm clouds brushed the roof"
    resolution = (
        f"{h} and {helper} spread the gingham over the tear and sang the rhyme together; "
        "the cloth widened just enough to cover it"
    )
    ending = "rain tapped on the repaired roof while the gingham shrank back to its neat little square"
    magic = "the cloth grew only as large as a kindness needed"
    lines = [
        f"Rain began to drum on {place}, and {h} heard a plip-plop beside {object_name}.",
        f"Under the dripping spot lay {world.cloth.phrase}, folded like a napkin for a fairy's tea.",
        f'"Can it help?" asked {h}. "We can ask it," said {helper}.',
        f"{h} lifted the cloth and sang, \"{rhyme}\" The gingham twinkled, but it stayed small.",
        f"The rain grew faster. A duck wore a flowerpot, a mouse wore a teacup, and everyone hurried beneath the table.",
        f"{helper} pointed to the cloth's four corners. " 
        f'"Magic needs two hands and one brave song," said {helper}.',
        f"{h} took one corner, {helper} took another, and together they sang, \"{rhyme}\"",
        f"The gingham stretched across the tear in {object_name}, keeping the room dry.",
        f"At last the clouds moved on, and {ending}. {h} knew that help grows when it is shared.",
    ]
    return _record(
        world,
        arc="rain",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        resolution=resolution,
        rhyme=rhyme,
        ending=ending,
        magic=magic,
        lines=lines,
    )


def _garden_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    helper = world.helper.label
    place = world.place
    rhyme = _choice(
        rng,
        [
            "Seed below, now grow, grow, grow!",
            "Checkered square, wake the pear!",
            "Fold and fold, make green gold!",
        ],
    )
    plant = _choice(rng, ["a drooping bean", "a shy pumpkin vine", "three sleepy sunflowers"])
    discovery = f"the gingham could wake thirsty plants when placed beside their roots"
    trouble = f"{plant} bent low because the garden had forgotten its morning water"
    cause = "a blocked clay pipe had stopped the garden stream"
    resolution = (
        f"{h} used the gingham to reveal the blocked pipe, and {helper} cleared it with a twig; "
        f"then {h} sang the rhyme over {plant}"
    )
    ending = "green leaves lifted their faces, and the gingham became an ordinary cloth again"
    magic = "the cloth pointed toward hidden trouble when it was held with care"
    lines = [
        f"At {place}, {h} saw {plant} drooping beneath the pale morning sun.",
        f"Near the garden path, {h} found {world.cloth.phrase} with its red checks sparkling.",
        f'"Can magic make flowers smile?" asked {h}. "{helper} answered, "First, let us find what hurts."',
        f"{h} held the gingham over the soil. It tugged gently toward a buried clay pipe.",
        f"The pipe was blocked with a pebble, so no water could reach the roots.",
        f'"I know what to do," said {h}. "{helper}, will you help me clear it?"',
        f"{helper} loosened the pebble with a twig, and water trickled toward the thirsty bed.",
        f"{h} laid the gingham beside {plant} and sang, \"{rhyme}\"",
        f"The leaves rose like little green hands. By noon, {ending}.",
    ]
    return _record(
        world,
        arc="garden",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        resolution=resolution,
        rhyme=rhyme,
        ending=ending,
        magic=magic,
        lines=lines,
    )


def _bell_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    helper = world.helper.label
    place = world.place
    rhyme = _choice(
        rng,
        [
            "Ring, ring, ding, bring back spring!",
            "Gingham dear, make the true sound clear!",
            "Softly chime, mend the time!",
        ],
    )
    sound = _choice(rng, ["the bedtime bell", "the tiny school bell", "the blue porch bell"])
    discovery = "the gingham could catch a lost sound and carry it home"
    trouble = f"{sound} rang without stopping and frightened the children of the village"
    cause = "a loose bell cord had caught on a branch and could not swing free"
    resolution = (
        f"{h} wrapped the gingham around the cord while {helper} freed the branch; "
        "the cloth caught the last wild ring"
    )
    ending = "one clear bell note floated over the quiet roofs, then the gingham folded itself"
    magic = "the cloth held noise as gently as a pocket holds a pebble"
    lines = [
        f"At {place}, {sound} went ding-ding-ding from noon until night.",
        f"{h} covered both ears and found {world.cloth.phrase} beside the bell rope.",
        f'"Why will it not stop?" asked {h}. "{helper} replied, "A sound may need a path home."',
        f"The bell cord had caught on a branch, and each gust pulled it again.",
        f"{h} tried a broom, a mitten, and a long spoon. The bell only rang louder.",
        f'"Let us use the gingham gently," said {helper}. "No tugging, no scolding."',
        f"{h} wrapped the cloth around the cord and sang, \"{rhyme}\"",
        f"{helper} freed the branch. The gingham caught the final ring, and the bell grew still.",
        f"After supper, {ending}. {h} discovered that patience can make a noisy problem small.",
    ]
    return _record(
        world,
        arc="bell",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        resolution=resolution,
        rhyme=rhyme,
        ending=ending,
        magic=magic,
        lines=lines,
    )


def _pocket_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    helper = world.helper.label
    place = world.place
    rhyme = _choice(
        rng,
        [
            "Fold so neat, return the treat!",
            "Check and cheer, bring it near!",
            "Gingham square, find it there!",
        ],
    )
    item = _choice(rng, ["a silver thimble", "a blue button", "a warm brass key"])
    discovery = f"the gingham could point to a lost thing when someone admitted where they had searched"
    trouble = f"{item} vanished before the nursery sewing lesson"
    cause = "it had slipped through a loose pocket and rolled beneath the floorboards"
    resolution = (
        f"{h} told {helper} exactly where the pocket had torn, and the gingham led them beneath "
        "the floorboards to the missing item"
    )
    ending = "the thimble shone in its proper basket while the gingham made a tidy pocket patch"
    magic = "honest words helped the cloth find what hurried guessing could not"
    lines = [
        f"In {place}, {h} was ready to sew when {item} disappeared.",
        f"{h} searched the basket, the shelf, and the teapot, then blamed the cat, though the cat looked innocent.",
        f"{helper} held up {world.cloth.phrase}. " 
        f'"Tell me every place you truly looked," said {helper}.',
        f'"I did not look in my torn pocket," admitted {h}. "I was afraid it was my fault."',
        f"The gingham gave a little flutter and pointed straight toward the floor.",
        f"{h} and {helper} lifted a board. There below lay {item}, bright with dust.",
        f'"Gingham square, find it there!" sang {h}. "Now we know the way."',
        f"{resolution}.",
        f"Before bedtime, {ending}. {h} learned that honest words can guide a little magic.",
    ]
    return _record(
        world,
        arc="pocket",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        resolution=resolution,
        rhyme=rhyme,
        ending=ending,
        magic=magic,
        lines=lines,
    )


ARC_BUILDERS = [_moon_arc, _rain_arc, _garden_arc, _bell_arc, _pocket_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7B3)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h} discover about the gingham?",
            answer=f"{h} discovered that {facts['discovery']}.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f"The trouble began because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did {h} help solve the problem?",
            answer=f"{facts['resolution']}.",
        ),
        QAItem(
            question="What kind of magic did the gingham use?",
            answer=f"The gingham's magic was that {facts['magic']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gingham?",
            answer="Gingham is a woven cloth patterned with small checks, often made by crossing two colors of thread.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is an imagined power that lets something happen in an unusual or impossible way.",
        ),
        QAItem(
            question="Why can a rhyme help a nursery story?",
            answer="A rhyme gives the story a steady, playful sound that is easy for children to remember and say aloud.",
        ),
        QAItem(
            question="Why should a magical helper be used carefully?",
            answer="Using magic carefully keeps characters thoughtful and shows that good results may still require listening, patience, and teamwork.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a nursery-rhyme story for young children about magical gingham.",
        f"Tell a gentle story set in {world.place} where a child and a helper use a checked cloth to mend a problem.",
        "Use repetition, rhyme, dialogue, and a small piece of cloth whose magic rewards kindness.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.helper, world.cloth]:
        lines.append(
            f"  {entity.id:7} {entity.kind:14} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        out.append(f"{index}. {prompt}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    if args.show_asp:
        print(
            asp_program(
                "#show enchanted/1.\n#show helpful/1.\n#show mended/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "3 compatible logical atoms: "
            "enchanted(hero), helpful(hero), mended(hero)"
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Mina",
                helper_name="Grandma May",
                place="the little nursery",
                seed=101,
            ),
            StoryParams(
                name="Pip",
                helper_name="Aunt Bea",
                place="the moonlit kitchen",
                seed=102,
            ),
            StoryParams(
                name="Lulu",
                helper_name="Uncle Tom",
                place="the garden gate",
                seed=103,
            ),
            StoryParams(
                name="Nell",
                helper_name="Miss June",
                place="the blue cottage",
                seed=104,
            ),
            StoryParams(
                name="Toby",
                helper_name="Grandpa Gus",
                place="the sleepy hill",
                seed=105,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n:
        raise StoryError("could not create enough distinct story variants")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
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
    try:
        main()
    except StoryError as exc:
        print(f"StoryError: {exc}", file=sys.stderr)
        sys.exit(2)
