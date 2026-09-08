#!/usr/bin/env python3
"""
A small mythic story world about an honest merchant, a difficult delivery,
and a message that must reach the right person before sunset.
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
import hashlib
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
    place: str = "the hill road"
    child: str = "Luna"
    merchant: str = "Mara"
    delivery: str = "a sealed blue letter"
    inform: str = "inform the bell keeper that the spring has returned"
    seed: Optional[int] = None


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"energy": 1.0, "distance": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"courage": 0.0, "trust": 0.0, "wonder": 0.0}
    )


@dataclass
class World:
    place: str
    child: Person
    merchant: Person
    delivery: str
    message: str = ""
    obstacle: str = ""
    clue: str = ""
    method: str = ""
    surprise: str = ""
    resolution: str = ""
    lesson: str = ""
    ending_image: str = ""
    delivered: bool = False
    informed: bool = False
    repeated: bool = False
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SCENES = [
    {
        "message": "The mountain spring is flowing again.",
        "obstacle": "A silver fog covered the forked road, and each fork seemed to lead to a different tower.",
        "clue": "A raven called once from the true road and twice from the false road.",
        "method": "Luna listened, counted the calls, and followed the single call toward the old bell tower.",
        "surprise": "The bell keeper was not an old man at all, but a shy fox wearing a brass key.",
        "resolution": "The fox unlocked the bell, and its note rolled from the hill to the thirsty village.",
        "lesson": "a careful listener can carry hope farther than a hurried traveler",
        "ending": "That evening, blue water shone in every village cup.",
        "items": ["blue letter", "brass key"],
    },
    {
        "message": "The moon orchard will bloom tonight.",
        "obstacle": "A bridge of woven vines had twisted above a deep ravine, leaving no safe path for a quick crossing.",
        "clue": "The vines tightened whenever Luna pulled them and loosened whenever she sang the merchant's old three-beat tune.",
        "method": "Luna sang softly, stepped only where the vines rested, and crossed one careful foot at a time.",
        "surprise": "On the far side, the orchard gate opened by itself because the trees had heard the tune.",
        "resolution": "Luna delivered the letter beneath the oldest tree, and the moon blossoms opened like little lamps.",
        "lesson": "patience can reveal a door that force would keep shut",
        "ending": "Petals drifted around the merchant's cart like stars that had learned to fall.",
        "items": ["blue letter", "moon blossom"],
    },
    {
        "message": "The king's lost bell is beneath the market hill.",
        "obstacle": "The road was crowded with noisy sellers, and a false merchant offered to carry the delivery away.",
        "clue": "The real merchant had tied three red threads around the letter case, while the stranger had none.",
        "method": "Luna checked the sign, asked the stranger to name the agreed password, and kept the delivery close.",
        "surprise": "The stranger was the king's disguised messenger, testing whether the village still guarded its promises.",
        "resolution": "Luna passed the letter only after the password was spoken, and the hidden bell rang below the hill.",
        "lesson": "trust grows from both kindness and careful checking",
        "ending": "By dawn, the market stalls were bright with bells instead of locks.",
        "items": ["threaded letter case", "market bell"],
    },
    {
        "message": "The river has changed its path.",
        "obstacle": "Rain had erased the road signs, and the delivery cart stood beside two streams that looked exactly alike.",
        "clue": "One stream carried willow leaves upstream, while the other carried them toward the valley.",
        "method": "Luna watched the leaves, marked the valley stream with white stones, and guided the merchant around the flooded bend.",
        "surprise": "The river had moved to protect a sleeping stone giant beneath the old road.",
        "resolution": "The message reached the ferryman, who moved the village crossing before nightfall.",
        "lesson": "small signs can reveal a large change",
        "ending": "The new river glittered around the giant's quiet stone toes.",
        "items": ["white stones", "sealed message"],
    },
]


NAMES = ["Luna", "Ivo", "Nera", "Tavi", "Suri"]
MERCHANTS = ["Mara", "Oren", "Bela", "Toma", "Yara"]
DELIVERIES = [
    "a sealed blue letter",
    "a red parcel tied with twine",
    "a small silver scroll",
    "a pouch of warm bread",
]
INFORM_OPTIONS = [
    "inform the bell keeper that the spring has returned",
    "inform the village that the moon orchard will bloom",
    "inform the watchman that the hidden bell has been found",
    "inform the ferryman that the river has changed its path",
]
PLACES = ["the hill road", "the moon market", "the cedar pass", "the river valley"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mythic merchant delivery story world.")
    parser.add_argument("--place", choices=PLACES, default=None)
    parser.add_argument("--child")
    parser.add_argument("--merchant")
    parser.add_argument("--delivery")
    parser.add_argument("--inform")
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
    place = args.place or rng.choice(PLACES)
    child = args.child or rng.choice(NAMES)
    merchant = args.merchant or rng.choice(MERCHANTS)
    delivery = args.delivery or rng.choice(DELIVERIES)
    inform = args.inform or rng.choice(INFORM_OPTIONS)
    if not child.strip() or not merchant.strip():
        raise StoryError("The child and merchant must both have names.")
    if "inform" not in inform.lower():
        raise StoryError("The inform field must describe an informing action.")
    return StoryParams(
        place=place,
        child=child,
        merchant=merchant,
        delivery=delivery,
        inform=inform,
    )


def choose_scene(params: StoryParams) -> dict:
    material = "|".join(
        [params.place, params.child, params.merchant, params.delivery, params.inform]
    )
    number = (
        params.seed
        if params.seed is not None
        else int.from_bytes(
            hashlib.blake2b(material.encode("utf-8"), digest_size=8).digest(), "big"
        )
    )
    return SCENES[number % len(SCENES)]


def generate_story(world: World, params: StoryParams) -> None:
    scene = choose_scene(params)
    world.message = scene["message"]
    world.obstacle = scene["obstacle"]
    world.clue = scene["clue"]
    world.method = scene["method"]
    world.surprise = scene["surprise"]
    world.resolution = scene["resolution"]
    world.lesson = scene["lesson"]
    world.ending_image = scene["ending"]

    child = world.child.name
    merchant = world.merchant.name
    place = world.place

    world.say(
        f"In the days when hills remembered names, {child} found {merchant}, a merchant, "
        f"waiting at {place} with {params.delivery} beneath her cloak."
    )
    world.say(
        f"\"Carry this delivery to the bell keeper, and inform the keeper that "
        f"{scene['message'].lower()}\" said {merchant}."
    )
    world.say(
        f"\"I will carry it, and I will tell it. I will carry it, and I will tell it,\" "
        f"{child} replied."
    )
    world.repeated = True
    world.message = scene["message"]
    world.child.memes["trust"] += 0.5
    world.merchant.memes["trust"] += 0.5
    world.child.meters["energy"] -= 0.1

    world.say(f"So {child} set out, while {merchant} watched the road and the red sun.")
    world.say(f"Before long, {scene['obstacle']}")
    world.say(
        f"{child} nearly chose the faster way, but {merchant} called, "
        f"\"A message has a mouth, but wisdom gives it ears.\""
    )
    world.say(
        f"{child} answered, \"Then I will listen before I leap.\" "
        f"{scene['clue']}"
    )
    world.say(scene["method"])
    world.say(f"Then came the surprise: {scene['surprise']}")
    world.say(
        f"The fox bowed, the gate opened, or the river shifted—yet in every telling, "
        f"{child} held the delivery safely and spoke the message clearly."
    )
    world.delivered = True
    world.informed = True
    world.child.memes["courage"] += 1.0
    world.child.memes["wonder"] += 1.0
    world.child.meters["distance"] += 1.0
    world.say(world.resolution)
    world.say(
        f"{merchant} arrived before the last light and asked, "
        f"\"What did the road teach you?\""
    )
    world.say(
        f"{child} replied, \"{scene['lesson'].capitalize()}. "
        f"I will remember it, and I will repeat it.\""
    )
    world.child.memes["trust"] += 0.5
    world.child.memes["courage"] += 0.5
    world.say(f"{scene['ending']} The delivery was complete, and the village slept unafraid.")


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    return [
        QAItem(
            question=f"Who gave {params.child} the delivery?",
            answer=f"{params.merchant}, the merchant, gave {params.child} {params.delivery}.",
        ),
        QAItem(
            question=f"What did {params.child} need to inform the bell keeper about?",
            answer=f"{params.child} needed to inform the bell keeper that {world.message.lower()}",
        ),
        QAItem(
            question="What made the delivery difficult?",
            answer=world.obstacle,
        ),
        QAItem(
            question="What clue helped the traveler choose wisely?",
            answer=world.clue,
        ),
        QAItem(
            question="What surprising thing happened?",
            answer=world.surprise,
        ),
        QAItem(
            question="How was the message finally delivered?",
            answer=world.resolution,
        ),
        QAItem(
            question=f"What did {params.child} learn?",
            answer=f"{params.child} learned that {world.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a merchant?",
            answer="A merchant is a person who buys, sells, or carries goods.",
        ),
        QAItem(
            question="What does delivery mean?",
            answer="Delivery means taking something safely to the person or place meant to receive it.",
        ),
        QAItem(
            question="Why should a message be checked before it is delivered?",
            answer="A message should be checked so it reaches the right person and keeps its meaning.",
        ),
    ]


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        f"Write a mythic story about {params.child} helping a merchant with a delivery.",
        f"Tell a child-friendly tale in {params.place} where someone must inform a keeper before sunset.",
        "Use rhyme, repetition, and a surprising turn in a story about carrying hope.",
    ]


def format_qa(sample: StorySample) -> str:
    sections = ["== Generation prompts =="]
    sections.extend(f"{i}. {text}" for i, text in enumerate(sample.prompts, 1))
    sections.append("")
    sections.append("== Story Q&A ==")
    for item in sample.story_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    sections.append("")
    sections.append("== World Q&A ==")
    for item in sample.world_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    return "\n".join(sections)


ASP_RULES = r"""
place(hill_road).
place(moon_market).
place(cedar_pass).
place(river_valley).
delivery(letter).
delivery(parcel).
delivery(scroll).
merchant_present.
inform_required.
rhyme_present.
repetition_present.
surprise_present.
valid_story :-
    merchant_present,
    delivery(_),
    inform_required,
    rhyme_present,
    repetition_present,
    surprise_present.
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("merchant_present"),
            asp.fact("delivery", "letter"),
            asp.fact("inform_required"),
            asp.fact("rhyme_present"),
            asp.fact("repetition_present"),
            asp.fact("surprise_present"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    valid = any(symbol.name == "valid_story" for symbol in model)
    if not valid:
        print("MISMATCH: ASP story gate failed.")
        return 1
    for seed in range(4):
        params = StoryParams(seed=seed)
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story is incomplete.")
            return 1
        if sample.world is None or not sample.world.delivered or not sample.world.informed:
            print("MISMATCH: delivery/inform state was not completed.")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = World(
        place=params.place,
        child=Person(params.child, "child"),
        merchant=Person(params.merchant, "merchant"),
        delivery=params.delivery,
    )
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
        print("--- world trace ---")
        print(asdict(sample.params))
        print(
            {
                "child_meters": sample.world.child.meters,
                "child_memes": sample.world.child.memes,
                "merchant_memes": sample.world.merchant.memes,
                "delivered": sample.world.delivered,
                "informed": sample.world.informed,
                "repeated": sample.world.repeated,
                "message": sample.world.message,
            }
        )
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        place="the hill road",
        child="Luna",
        merchant="Mara",
        delivery="a sealed blue letter",
        inform="inform the bell keeper that the spring has returned",
        seed=0,
    ),
    StoryParams(
        place="the moon market",
        child="Ivo",
        merchant="Oren",
        delivery="a red parcel tied with twine",
        inform="inform the village that the moon orchard will bloom",
        seed=1,
    ),
    StoryParams(
        place="the cedar pass",
        child="Nera",
        merchant="Bela",
        delivery="a small silver scroll",
        inform="inform the watchman that the hidden bell has been found",
        seed=2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        raise SystemExit(asp_verify())

    if args.show_asp:
        print(asp_program())
        return

    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        print("ASP model:", asp.one_model(asp_program()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
