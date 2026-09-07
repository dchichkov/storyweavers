#!/usr/bin/env python3
"""Gingham Magic: a nursery-rhyme tale about a small spell and a brave repair."""

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
    kind: str
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
    child: str = "Mira"
    helper: str = "Pip"
    color: str = "red"
    object_name: str = "basket"
    rhyme: str = "bright"
    seed: int = 777


NAMES = ("Mira", "Nell", "Toby", "Lina", "Owen", "Pip")
COLORS = ("red", "blue", "yellow")
OBJECTS = {
    "basket": ("a little basket", "the garden gate"),
    "bonnet": ("a gingham bonnet", "the apple tree"),
    "blanket": ("a gingham blanket", "the moonlit porch"),
}
RHYMES = ("bright", "sweet", "round")


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "child": Entity(
                "child", params.child, "character", "cottage",
                memes={"courage": 0.5, "worry": 0.5},
            ),
            "helper": Entity(
                "helper", params.helper, "character", "cottage",
                memes={"kindness": 0.8},
            ),
            "cloth": Entity(
                "cloth", f"{params.color} gingham", "magical_cloth", "cottage",
                meters={"magic": 1, "torn": 0, "glow": 0},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(
        self,
        kind: str,
        text: str,
        *,
        question: str = "",
        cause: str = "",
        result: str = "",
    ) -> None:
        self.history.append(
            Event(
                kind=kind,
                text=text,
                question=question,
                cause=cause,
                result=result,
                state=self.snapshot(),
            )
        )


PROMPT = (
    "Write a gentle nursery-rhyme story about a child, gingham cloth, "
    "and a small magic problem solved with care."
)

ASP_RULES = """
works(Color, Object) :- cloth(Color), object(Object), matching(Color,Object).
matching(red,basket).
matching(blue,bonnet).
matching(yellow,blanket).
#show works/2.
"""


def valid_combos() -> list[tuple[str, str]]:
    return [("red", "basket"), ("blue", "bonnet"), ("yellow", "blanket")]


def asp_facts() -> str:
    from asp import fact
    colors = "\n".join(fact("cloth", color) for color in COLORS)
    objects = "\n".join(fact("object", name) for name in OBJECTS)
    return colors + "\n" + objects


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    return set(atoms(model, "works"))


def validate_params(params: StoryParams) -> None:
    if (params.color, params.object_name) not in valid_combos():
        raise StoryError(
            f"The {params.color} gingham does not match the {params.object_name}; "
            "choose a matching magical pair."
        )
    if params.child == params.helper:
        raise StoryError("The child and helper need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.child, params.helper)):
        raise StoryError("Names must be simple capitalized names.")
    if params.rhyme not in RHYMES:
        raise StoryError("Unknown rhyme choice.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    object_label, place = OBJECTS[params.object_name]
    world.entities["object"] = Entity(
        "object",
        object_label,
        "thing",
        place,
        meters={"safe": 0, "needed": 1},
    )
    return world


def mend_cloth(world: World) -> None:
    cloth = world.entities["cloth"]
    child = world.entities["child"]
    if cloth.meters["torn"] != 1:
        raise StoryError("The magical cloth must be torn before it can be mended.")
    if child.memes["courage"] < 1:
        raise StoryError("The child needs courage before trying the repair.")
    cloth.meters.update(torn=0, glow=1)
    child.memes["worry"] = 0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child = world.entities["child"]
    helper = world.entities["helper"]
    cloth = world.entities["cloth"]
    item = world.entities["object"]
    name = child.label
    friend = helper.label
    color = params.color
    object_label, place = OBJECTS[params.object_name]

    world.narrate(
        "beginning",
        f"{name} wore {color} gingham, neat and trim, "
        f"and carried {object_label} with a humming little whim. "
        f"At the {place}, the morning bells began to chime.",
    )

    world.narrate(
        "problem",
        f"A thorn caught the gingham with a tiny, sharp snap. "
        f"The magic cloth tore, and the basket's safe path went flat.",
        question="Why did the magic stop working?",
        cause=f"The thorn tore {name}'s {color} gingham cloth.",
        result=f"The cloth lost its glow, so {object_label} could not travel safely.",
    )
    cloth.meters["torn"] = 1
    cloth.meters["magic"] = 0
    item.meters["safe"] = 0
    child.memes["worry"] = 1

    world.narrate(
        "turn",
        f"{friend} came near and said, \"A spell is not a thing to hide. "
        f"Find the tear, hold it gently, and let courage be your guide.\"",
    )
    child.memes["courage"] = 1
    world.narrate(
        "help",
        f"{name} looked closely. {friend} held the cloth steady while "
        f"{name} matched each little check to check.",
        question="How did the helper make the repair possible?",
        cause=f"{friend} held the gingham still while {name} worked carefully.",
        result="The child could line up the torn checks instead of pulling the cloth apart.",
    )

    mend_cloth(world)
    item.location = place
    item.meters["safe"] = 1
    world.narrate(
        "magic",
        f"Stitch, stitch, {color} and bright; the gingham shone with gentle light. "
        f"The magic woke, a warm small spark, and guided {object_label} through the dark.",
        question="What repaired the magic?",
        cause=f"{name} joined the torn gingham checks with patience and courage.",
        result="The cloth glowed again and made the path safe.",
    )

    world.narrate(
        "ending",
        f"They reached the {place} before the sun grew low. "
        f"{object_label} rested safe, and the gingham gave one cheerful glow. "
        f"Then all sang, \"Care can mend what fear may tear; "
        f"a steady heart makes magic fair.\"",
        question="What changed by the end of the story?",
        cause="The child stopped hiding from the torn cloth and repaired it with help.",
        result=f"The magic returned, and {object_label} reached the {place} safely.",
    )

    sample = StorySample(
        params=params,
        story="\n\n".join(event.text for event in world.history),
        prompts=[PROMPT],
        story_qa=[
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history
            if event.question
        ],
        world_qa=[
            QAItem(
                "What is gingham?",
                "Gingham is cloth woven in a checked pattern.",
            ),
            QAItem(
                "What helps a small magic problem in this story?",
                "Care, courage, and a helpful friend make the repair possible.",
            ),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample) -> None:
    world = sample.world
    cloth = world.entities["cloth"]
    item = world.entities["object"]
    if cloth.meters["torn"] or cloth.meters["glow"] != 1:
        raise StoryError("The gingham must be mended and glowing at the ending.")
    if item.meters["safe"] != 1:
        raise StoryError("The magical object must reach a safe destination.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs several grounded questions and answers.")
    if len(sample.story.split()) < 100:
        raise StoryError("The story needs a complete beginning, turn, and ending.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--helper")
    parser.add_argument("--color", choices=COLORS)
    parser.add_argument("--object", dest="object_name", choices=tuple(OBJECTS))
    parser.add_argument("--rhyme", choices=RHYMES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    pairs = [
        pair for pair in valid_combos()
        if args.color is None or pair[0] == args.color
        if args.object_name is None or pair[1] == args.object_name
    ]
    if not pairs:
        raise StoryError("No matching gingham and magical object choices remain.")
    color, object_name = rng.choice(pairs)
    child = args.child or rng.choice(NAMES)
    helper = args.helper or rng.choice([name for name in NAMES if name != child])
    params = StoryParams(
        child=child,
        helper=helper,
        color=color,
        object_name=object_name,
        rhyme=args.rhyme or rng.choice(RHYMES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify() -> None:
    if asp_combos() != set(valid_combos()):
        raise StoryError("Python and ASP disagree about matching magical pairs.")
    count = 0
    for color, object_name in valid_combos():
        for rhyme in RHYMES:
            sample = generate(
                StoryParams(
                    child="Mira",
                    helper="Pip",
                    color=color,
                    object_name=object_name,
                    rhyme=rhyme,
                )
            )
            check_sample(sample)
            count += 1
    print(f"OK: {count} story states; {len(valid_combos())} matching pairs.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(
            json.dumps(
                {
                    "entities": sample.world.snapshot(),
                    "history": [asdict(event) for event in sample.world.history],
                },
                indent=2,
            )
        )


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
            for color, object_name in valid_combos():
                if args.color and args.color != color:
                    continue
                if args.object_name and args.object_name != object_name:
                    continue
                namespace = argparse.Namespace(**vars(args))
                namespace.color = color
                namespace.object_name = object_name
                params_list.append(resolve_params(namespace, rng))
            if not params_list:
                raise StoryError("No combinations match the selected options.")
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
