#!/usr/bin/env python3
"""
A heartwarming little yam storyworld with gentle humor.

Luna wants to bring the biggest yam to the village supper, but the yam has
other plans. A silly mishap becomes a chance for neighbors to help, laugh, and
share what matters.
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
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    child: str = "Luna"
    helper: str = "Grandma"
    place: str = "the village garden"
    yam_size: str = "enormous"
    humor: str = "a yam rolls away wearing a ribbon"
    lesson: str = "sharing makes an ordinary supper special"
    seed: Optional[int] = None


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"energy": 1.0, "warmth": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"kindness": 0.0, "humor": 0.0, "confidence": 0.0}
    )


@dataclass
class Yam:
    description: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"weight": 0.9, "dirt": 0.6}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"pride": 0.5, "shared_joy": 0.0}
    )


@dataclass
class World:
    place: str
    child: Person
    helper: Person
    yam: Yam
    event: str = ""
    obstacle: str = ""
    clue: str = ""
    first_attempt: str = ""
    action: str = ""
    resolution: str = ""
    lesson: str = ""
    ending_image: str = ""
    laughed: bool = False
    accepted_help: bool = False
    supper_shared: bool = False
    transformed: bool = False
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


NAME_POOL = ["Luna", "Milo", "Nia", "Pip", "Tessa", "Arlo"]
HELPER_POOL = ["Grandma", "Uncle Jo", "Aunt May", "Papa", "Neighbor Bea"]
SIZE_POOL = ["enormous", "round", "lumpy", "long", "comically wide"]
HUMOR_POOL = [
    "a yam rolls away wearing a ribbon",
    "the yam lands in a basket like it planned the trip",
    "a chicken follows the yam as if it were a parade leader",
    "the yam gets stuck in a flour sack and looks like a sleepy ghost",
    "the yam makes three small bumps before settling beside the soup pot",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming yam humor storyworld.")
    parser.add_argument("--child")
    parser.add_argument("--helper")
    parser.add_argument("--place", default="the village garden")
    parser.add_argument("--yam-size", choices=SIZE_POOL)
    parser.add_argument("--humor")
    parser.add_argument("--lesson")
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
    if args.place != "the village garden":
        raise StoryError("This yam world only supports the village garden setting.")
    return StoryParams(
        child=args.child or rng.choice(NAME_POOL),
        helper=args.helper or rng.choice(HELPER_POOL),
        place=args.place,
        yam_size=args.yam_size or rng.choice(SIZE_POOL),
        humor=args.humor or rng.choice(HUMOR_POOL),
        lesson=args.lesson or "sharing makes an ordinary supper special",
    )


def make_world(params: StoryParams) -> World:
    return World(
        place=params.place,
        child=Person(params.child, "child"),
        helper=Person(params.helper, "helper"),
        yam=Yam(params.yam_size),
    )


def generate_story(world: World, params: StoryParams) -> None:
    if params.seed is None:
        seed_value = sum(ord(char) for char in "|".join(asdict(params).values() if False else [
            params.child,
            params.helper,
            params.place,
            params.yam_size,
            params.humor,
            params.lesson,
        ]))
    else:
        seed_value = params.seed

    turns = [
        {
            "event": "the garden supper was almost ready",
            "obstacle": "the yam was so large that Luna could barely lift it without wobbling like a spoon in pudding",
            "clue": "a broad garden tray rested beside the bean trellis",
            "first": "tried to carry the yam alone",
            "action": "Luna and Grandma slid the yam onto the tray and carried it together",
            "result": "the yam reached the kitchen without a single toe being squashed",
            "ending": "the yam sat in the soup pot like a plump moon",
        },
        {
            "event": "the village was preparing its shared supper",
            "obstacle": "the yam slipped from Luna's arms and began rolling downhill",
            "clue": "a line of empty baskets curved toward the picnic table",
            "first": "chased after the yam with both arms waving",
            "action": "Luna and Grandma placed baskets across the path and gently guided the yam into the last one",
            "result": "the runaway yam stopped safely beside the supper table",
            "ending": "the yam rested in a basket while everyone pretended it had arrived on purpose",
        },
        {
            "event": "Luna wanted to present the garden's finest harvest",
            "obstacle": "the yam was too wide for the little kitchen door",
            "clue": "the side door stood open near the woodpile",
            "first": "pushed the yam toward the doorway and got stuck with it",
            "action": "Luna and Grandma used the side door and rolled the yam over a clean cloth",
            "result": "the yam entered the kitchen while Luna escaped with only flour on her nose",
            "ending": "the yam steamed on the table beneath a floury fingerprint",
        },
    ]
    turn = turns[seed_value % len(turns)]

    world.event = turn["event"]
    world.obstacle = turn["obstacle"]
    world.clue = turn["clue"]
    world.first_attempt = turn["first"]
    world.action = turn["action"]
    world.resolution = turn["result"]
    world.ending_image = turn["ending"]
    world.lesson = params.lesson

    world.say(
        f"In {params.place}, {params.child} found a {params.yam_size} yam just before supper."
    )
    world.child.memes["confidence"] += 0.4
    world.yam.memes["pride"] += 0.2
    world.say(
        f"\"This yam is perfect for our shared meal,\" said {params.child}. "
        f"\"It is also large enough to need its own chair,\" replied {params.helper}."
    )
    world.laughed = True
    world.child.memes["humor"] += 0.8
    world.helper.memes["humor"] += 0.5

    world.say(
        f"Then {turn['event']}, but {turn['obstacle']}."
    )
    world.say(
        f"At first, {params.child} {turn['first']}. "
        f"\"Maybe the yam wants to help us instead of being carried,\" "
        f"{params.helper} said. \"Yams can be very opinionated.\""
    )
    world.say(
        f"{params.child} looked carefully and noticed that {turn['clue']}."
    )
    world.say(
        f"\"I know what to do now,\" said {params.child}. "
        f"\"Good thinking,\" said {params.helper}. \"And I promise not to interview the yam.\""
    )
    world.accepted_help = True
    world.child.memes["kindness"] += 0.8
    world.helper.memes["kindness"] += 0.5
    world.say(f"{turn['action']}.")
    world.say(f"{turn['result']}.")
    world.yam.meters["dirt"] = 0.1
    world.yam.memes["shared_joy"] += 1.0
    world.child.meters["energy"] -= 0.2

    world.say(
        f"At supper, {params.child} cut the yam into enough pieces for everyone, "
        f"including the neighbor who had brought the warm bread."
    )
    world.supper_shared = True
    world.child.memes["kindness"] += 1.0
    world.helper.memes["kindness"] += 0.5
    world.yam.memes["shared_joy"] += 0.8
    world.say(
        f"{params.child} learned that {params.lesson}. "
        f"{turn['ending']}."
    )
    world.transformed = True
    world.child.memes["confidence"] += 0.5
    world.child.meters["warmth"] += 1.0


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    return [
        QAItem(
            question=f"Where did {params.child} find the yam?",
            answer=f"{params.child} found the yam in {params.place}.",
        ),
        QAItem(
            question=f"Why was the yam difficult for {params.child} to handle?",
            answer=f"The yam was {params.yam_size}, so {params.child} could not manage it easily alone.",
        ),
        QAItem(
            question=f"What funny thing happened with the yam?",
            answer=f"{params.humor.capitalize()}, which made {params.child} and {params.helper} laugh while they solved the problem.",
        ),
        QAItem(
            question=f"How did {params.helper} help {params.child}?",
            answer=f"{params.helper} helped {params.child} notice {world.clue} and work out a safe way to move the yam.",
        ),
        QAItem(
            question=f"How did {params.child} change during the story?",
            answer=f"{params.child} accepted help, used careful thinking, and shared the yam so the whole village could enjoy supper.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"The yam reached supper safely, was shared with everyone, and {world.ending_image}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a yam?",
            answer="A yam is an edible root vegetable that grows underground.",
        ),
        QAItem(
            question="Why might people share food?",
            answer="People share food to care for one another and make a meal more joyful.",
        ),
        QAItem(
            question="Why can humor help during a problem?",
            answer="Gentle humor can help people stay calm, notice possibilities, and work together.",
        ),
    ]


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        f"Write a heartwarming story about {params.child} finding a {params.yam_size} yam in {params.place}.",
        f"Tell a funny, child-friendly story where {params.child} and {params.helper} solve a yam problem together.",
        f"Write a gentle story showing that {params.lesson}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
place(village_garden).
vegetable(yam).
has_humor.
heartwarming.
valid_story :- place(village_garden), vegetable(yam), has_humor, heartwarming.
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "village_garden"),
            asp.fact("vegetable", "yam"),
            asp.fact("has_humor"),
            asp.fact("heartwarming"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/0."))
    if any(symbol.name == "valid_story" for symbol in model):
        print("OK: ASP yam story gate is satisfiable.")
        return 0
    print("MISMATCH: ASP yam story gate did not produce a model.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    world.facts["params"] = params
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(params),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        world = sample.world
        print("--- world trace ---")
        print(asdict(sample.params))
        print(
            {
                "child": world.child.meters | world.child.memes,
                "helper": world.helper.meters | world.helper.memes,
                "yam": world.yam.meters | world.yam.memes,
                "laughed": world.laughed,
                "accepted_help": world.accepted_help,
                "supper_shared": world.supper_shared,
                "transformed": world.transformed,
            }
        )
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        child="Luna",
        helper="Grandma",
        yam_size="enormous",
        humor="a yam rolls away wearing a ribbon",
    ),
    StoryParams(
        child="Milo",
        helper="Aunt May",
        yam_size="comically wide",
        humor="a chicken follows the yam as if it were a parade leader",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return

    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        print("ASP model:", asp.one_model(asp_program("#show valid_story/0.")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, params in enumerate(CURATED):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        for index in range(args.n):
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
