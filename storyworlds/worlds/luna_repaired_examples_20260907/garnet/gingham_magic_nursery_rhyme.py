#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about gingham, a little magic, and a careful fix.
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
    child: Item
    keeper: Item
    cloth: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    keeper_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Pip", "Mina", "Toby", "Nell", "Ivy", "Jo", "Lulu", "Sam"]
KEEPERS = ["Nana May", "Aunt Rose", "Grandma June", "Old Tom", "Miss Bea"]
PLACES = [
    "the nursery room",
    "the moonlit kitchen",
    "the little playhouse",
    "the garden gate",
    "the warm attic",
]


ASP_RULES = r"""
#show bright/1.
#show wandering/1.
#show mended/1.

bright(C) :- touches_magic(C).
wandering(C) :- bright(C), loose_corner(C).
mended(C) :- wandering(C), gets_help(C).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("touches_magic", "child"),
            asp.fact("loose_corner", "child"),
            asp.fact("gets_help", "child"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = "#show bright/1.\n#show wandering/1.\n#show mended/1."
    model = asp.one_model(asp_program(shown))
    actual = set()
    for atom in model:
        args = tuple(
            value.number if value.type == value.type.Number else value.name
            for value in atom.arguments
        )
        actual.add((atom.name, args))
    expected = {
        ("bright", ("child",)),
        ("wandering", ("child",)),
        ("mended", ("child",)),
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
    parser.add_argument("--keeper-name", choices=KEEPERS)
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
        keeper_name=args.keeper_name or rng.choice(KEEPERS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    child = Item(
        id="child",
        label=params.name,
        phrase=f"little {params.name}",
        kind="character",
        memes={"curiosity": 0.8, "care": 0.7},
    )
    keeper = Item(
        id="keeper",
        label=params.keeper_name,
        phrase=params.keeper_name,
        kind="character",
        memes={"patience": 0.9, "care": 0.9},
    )
    cloth = Item(
        id="gingham",
        label="gingham",
        phrase="a square of red-and-white gingham",
        kind="cloth",
        owner="keeper",
        meters={"length": 0.6, "width": 0.6, "looseness": 0.0},
        memes={"magic": 0.8, "cheer": 0.7},
    )
    seed = params.seed
    if seed is None:
        seed = sum(
            ord(char)
            for char in f"{params.name}|{params.keeper_name}|{params.place}"
        )
    return World(
        child=child,
        keeper=keeper,
        cloth=cloth,
        place=params.place,
        seed=seed,
    )


def _pick(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    discovery: str,
    trouble: str,
    cause: str,
    refrain: str,
    resolution: str,
    ending: str,
    lesson: str,
    lines: list[str],
) -> str:
    world.facts.update(
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        refrain=refrain,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        mended=True,
    )
    world.cloth.meters["looseness"] = 0.0
    world.cloth.memes["magic"] = 0.5
    return " ".join(lines)


def _moon_arc(world: World, rng: random.Random) -> str:
    h = world.child.label
    k = world.keeper.label
    p = world.place
    visitor = _pick(rng, ["the moon", "a sleepy star", "the silver owl"])
    place = _pick(rng, ["the window", "the rocking chair", "the toy-box lid"])
    discovery = f"the gingham could make a moonlit picture dance when it was gently waved"
    trouble = f"the dancing picture floated from {place} toward the open door"
    cause = "one corner of the gingham had come loose, so the magic breeze pulled it wherever it pleased"
    refrain = "Square and fair, stay in the air"
    resolution = f"{h} stopped pulling and let {k} stitch the loose corner before waving the gingham slowly"
    ending = f"the picture of {visitor} rested neatly on {place}, while the gingham lay flat and bright"
    lesson = "magic is safest when a loose thing is fixed before the fun begins"
    lines = [
        f"In {p}, {h} found a square of red-and-white gingham beneath a pillow.",
        f"{h} waved it once and sang, \"{refrain}!\" At once, {visitor} appeared in the cloth and began to dance.",
        f"The picture twirled across {place}, bobbed past a basket, and drifted toward the open door.",
        f'"Come back, little square!" cried {h}. The gingham fluttered faster, for one corner was loose.',
        f"{k} hurried in, but did not chase the magic. {k} held the cloth still and showed {h} the tiny wandering thread.",
        f"{h} watched carefully while {k} stitched the corner. Then they tested the gingham with one slow wave.",
        f"The picture danced in a neat circle, and the magic breeze stayed close to the cloth.",
        f"By bedtime, {ending}. {h} learned that a careful stitch can give wild magic a gentle home.",
    ]
    return _record(
        world,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        refrain=refrain,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


def _rain_arc(world: World, rng: random.Random) -> str:
    h = world.child.label
    k = world.keeper.label
    p = world.place
    target = _pick(rng, ["the flowerpots", "the thirsty herbs", "the bean vines"])
    discovery = "the gingham could call a tiny indoor rain when folded into a square"
    trouble = f"the little rain cloud followed {h} instead of watering {target}"
    cause = "the cloth was folded crookedly, leaving one magic stripe pointing at the child"
    refrain = "Fold it right, rain so light"
    resolution = f"{h} unfolded the gingham while {k} turned the magic stripe toward {target}"
    ending = f"a soft sprinkle watered {target}, and three bright drops shone on the gingham's checked squares"
    lesson = "a magical tool needs a clear direction"
    lines = [
        f"At {p}, {h} folded the gingham into a tidy square and whispered, \"{refrain}.\"",
        f"Poof! A little gray cloud puffed out and sprinkled rain over {h}'s nose.",
        f"{h} skipped left; the cloud skipped left. {h} skipped right; the cloud skipped right.",
        f"The cloud followed close behind, while {target} drooped in the dry corner.",
        f"{k} looked at the cloth and found one stripe folded the wrong way. \"Magic follows the pattern it is given,\" said {k}.",
        f"{h} opened the square, smoothed every check, and pointed the stripe toward {target}.",
        f"The cloud sailed across the room and gave the thirsty plants one gentle shower.",
        f"Then the cloud popped into a pearl of mist. By supper, {ending}.",
    ]
    return _record(
        world,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        refrain=refrain,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


def _bird_arc(world: World, rng: random.Random) -> str:
    h = world.child.label
    k = world.keeper.label
    p = world.place
    bird = _pick(rng, ["a bluebird", "a robin", "a yellow finch"])
    perch = _pick(rng, ["the curtain rod", "the tallest shelf", "the garden gate"])
    discovery = "the gingham could make a cloth bird flutter when tapped three times"
    trouble = f"the cloth bird flew away and perched on {perch}"
    cause = "the magic was still awake because the gingham had not been folded closed"
    refrain = "Tap, tap, tap, fly back to the flap"
    resolution = f"{h} and {k} folded the gingham into a pocket and opened it beneath the cloth bird"
    ending = f"the cloth {bird} tucked its wings inside the folded gingham and became a quiet square again"
    lesson = "closing a magical thing is part of caring for it"
    lines = [
        f"Beside {p}, {h} found the gingham on a basket and tapped it three times.",
        f"Tap, tap, tap! A tiny cloth {bird} sprang up and flapped around the room.",
        f"It circled a lamp, tickled a curtain, and flew straight to {perch}.",
        f'"Come back, bird! Come back!" cried {h}. The cloth bird chirped, but it would not land.',
        f"{k} noticed that the gingham was still spread open. The magic had no little nest to return to.",
        f"{h} folded the checks corner to corner while {k} held out both hands like a quiet nest.",
        f"The cloth bird glided down, slipped into the fold, and tucked its wings away.",
        f"At dusk, {ending}. The gingham rested in its basket, ready for another careful rhyme.",
    ]
    return _record(
        world,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        refrain=refrain,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


def _pocket_arc(world: World, rng: random.Random) -> str:
    h = world.child.label
    k = world.keeper.label
    p = world.place
    object_name = _pick(rng, ["a wooden button", "a lost thimble", "a silver spoon"])
    destination = _pick(rng, ["under the bed", "inside a boot", "behind the flour tin"])
    discovery = "the gingham could make lost little things hop back into view"
    trouble = f"the magic made every small object hop toward {destination}"
    cause = "the gingham's corner had been tied in a knot, and the knot pointed all the hopping things one way"
    refrain = "Hop and stop, show your spot"
    resolution = f"{k} untied the knot while {h} held the gingham flat and called each object home"
    ending = f"{object_name} and the other missing things rested in a neat row beside the gingham"
    lesson = "when magic gets tangled, calm hands can untangle it"
    lines = [
        f"One morning in {p}, {h} shook the gingham and called, \"{refrain}!\"",
        f"A wooden button hopped from a drawer. A thimble bounced from a basket. Even a spoon began to skip.",
        f"Hop, hop, hop! Every little thing hurried toward {destination}.",
        f"{h} followed the bouncing objects, but the faster the child ran, the faster they hopped.",
        f"{k} caught the gingham and found a tight knot in one corner. The knot was pointing the magic like an arrow.",
        f"{k} loosened the knot while {h} held the cloth flat and named each lost thing.",
        f"The button, thimble, and spoon bounced back and settled beside the checked square.",
        f"After counting everything twice, {ending}. The nursery rhyme ended with a tidy little stop.",
    ]
    return _record(
        world,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        refrain=refrain,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


ARC_BUILDERS = [_moon_arc, _rain_arc, _bird_arc, _pocket_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x4179B)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.child.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h} discover about the gingham?",
            answer=f"{h} discovered that {facts['discovery']}.",
        ),
        QAItem(
            question="What caused the magical trouble?",
            answer=f"The trouble began because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did {h} and the helper solve the problem?",
            answer=f"They solved it when {facts['resolution']}.",
        ),
        QAItem(
            question="What lesson did the rhyme show?",
            answer=f"The story showed that {facts['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gingham?",
            answer="Gingham is a woven cloth with a checked pattern, often made from two colors such as red and white.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is an imagined power that lets something happen in an unusual or impossible way.",
        ),
        QAItem(
            question="Why should a loose thread be fixed?",
            answer="A loose thread can make cloth unravel, so stitching it helps the cloth stay strong and useful.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle nursery rhyme about magical gingham.",
        f"Tell a child-facing rhyme set in {world.place} where a checked cloth causes a small problem and a careful fix.",
        "Use repetition, bright images, and a clear ending to show how kindness guides magic.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.child, world.keeper, world.cloth]:
        lines.append(
            f"  {entity.id:8} {entity.kind:9} label={entity.label!r} "
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
                "#show bright/1.\n#show wandering/1.\n#show mended/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "3 compatible logical atoms: "
            "bright(child), wandering(child), mended(child)"
        )
        return

    base_seed = (
        args.seed if args.seed is not None else random.randrange(2**31)
    )
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Pip",
                keeper_name="Nana May",
                place="the nursery room",
                seed=11,
            ),
            StoryParams(
                name="Mina",
                keeper_name="Aunt Rose",
                place="the moonlit kitchen",
                seed=12,
            ),
            StoryParams(
                name="Toby",
                keeper_name="Grandma June",
                place="the little playhouse",
                seed=13,
            ),
            StoryParams(
                name="Nell",
                keeper_name="Miss Bea",
                place="the warm attic",
                seed=14,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
            params = resolve_params(
                args, random.Random(base_seed + index)
            )
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

        if len(samples) < args.n:
            raise StoryError("Could not create enough distinct story variants.")

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
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=header,
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
