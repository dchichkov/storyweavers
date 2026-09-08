#!/usr/bin/env python3
"""
A small mythic story world about quartz, a lost mitt, and the kindness that
helps a mountain village hear its own rhyme again.
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
    place: str = "the valley beneath the singing mountain"
    child: str = "Luna"
    companion: str = "Rook"
    quest: str = "return a lost mitt to its owner"
    transformation: str = "kind"
    seed: Optional[int] = None


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"warmth": 1.0, "energy": 1.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"kindness": 0.0, "courage": 0.0, "wonder": 0.0}
    )


@dataclass
class World:
    place: str
    child: Person
    companion: Person
    quartz_present: bool = False
    mitt_found: bool = False
    mitt_owner: str = ""
    rhyme_awakened: bool = False
    kindness_shown: bool = False
    challenge: str = ""
    clue: str = ""
    first_attempt: str = ""
    resolution: str = ""
    ending_image: str = ""
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


TALES = [
    {
        "owner": "the shepherd child Tavi",
        "challenge": (
            "A single woolen mitt lay beside a stream, but the stream had begun "
            "to rise around it."
        ),
        "clue": (
            "A thumb-shaped print in the frost led from the mitt toward a cave "
            "where a small bell was ringing."
        ),
        "first_attempt": (
            "reached toward the water, then stopped when a loose stone slipped "
            "underfoot"
        ),
        "action": (
            "Luna tied a scarf to Rook's walking staff, and together they made "
            "a long loop that lifted the mitt from the bank without entering "
            "the swift water."
        ),
        "resolution": (
            "Inside the cave they found Tavi shivering beside a trapped lamb, "
            "so Luna gave Tavi the warm mitt and helped guide the lamb out."
        ),
        "lesson": (
            "kindness warms more than the hand that first receives it"
        ),
        "ending": (
            "That night the quartz shone beside the hearth, and every bell in "
            "the valley answered in the same bright rhyme."
        ),
        "quartz": "a pale piece of quartz",
    },
    {
        "owner": "the old gatekeeper Mara",
        "challenge": (
            "A red mitt hung from a thorn bush below the moon road, while "
            "snow clouds gathered over the pass."
        ),
        "clue": (
            "Tiny quartz grains glittered in a line from the bush to the "
            "gatekeeper's abandoned lantern."
        ),
        "first_attempt": (
            "pulled at the thorn, then noticed that the wool was caught on a "
            "second branch and might tear"
        ),
        "action": (
            "Luna wrapped her sleeve around the thorns and used a fallen reed "
            "to loosen the wool one strand at a time."
        ),
        "resolution": (
            "The mitt belonged to Mara, whose fingers had gone numb while she "
            "searched for a lost traveler; with both hands warm again, she "
            "opened the safe gate and called the traveler home."
        ),
        "lesson": (
            "a careful kindness can open a way for many people"
        ),
        "ending": (
            "The quartz flashed on the gatepost, and the mountain wind repeated "
            "Luna's little rhyme all the way to dawn."
        ),
        "quartz": "a moon-white piece of quartz",
    },
    {
        "owner": "the cloud-weaver Nemi",
        "challenge": (
            "A blue mitt floated in a puddle beneath the cloud-weaver's bridge, "
            "where each ripple carried a half-finished song."
        ),
        "clue": (
            "The puddle reflected a bright quartz shard pointing toward the "
            "bridge's loose plank."
        ),
        "first_attempt": (
            "stepped onto the plank, then backed away when it groaned over the "
            "deep ravine"
        ),
        "action": (
            "Rook anchored a rope to an old stone, and Luna used the rope to "
            "reach the mitt from the safe side."
        ),
        "resolution": (
            "Nemi had dropped the mitt while saving a nest of cloud-swifts; "
            "Luna returned it, and Nemi used its soft lining to carry the tiny "
            "birds until they could fly."
        ),
        "lesson": (
            "kindness grows when one person notices another person's quiet work"
        ),
        "ending": (
            "The quartz shard became a star above the bridge, and the cloud-swifts "
            "wove Luna's rhyme through the evening mist."
        ),
        "quartz": "a clear piece of quartz",
    },
]


OPENINGS = [
    "In the first age, when mountains still remembered every promise",
    "Long ago, beneath a sky where stars spoke in silver syllables",
    "At the edge of an old valley, when the moon was young",
    "Before the village had a clock, a crown, or a written law",
    "In an age when stones could listen and rivers could answer",
]

RHYMES = [
    "Find what is lost, and let warmth be shared.",
    "A careful hand makes a frightened world less scared.",
    "When one heart listens, another heart is spared.",
    "Give back the warmth that someone else prepared.",
    "Kind words are small, but their shelter is wide.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Quartz mitt myth story world.")
    ap.add_argument(
        "--place",
        choices=["the valley beneath the singing mountain"],
        default="the valley beneath the singing mountain",
    )
    ap.add_argument("--child")
    ap.add_argument("--companion")
    ap.add_argument("--quest")
    ap.add_argument("--transformation")
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


NAME_POOL = ["Luna", "Mira", "Orin", "Sela", "Tarin", "Nia"]
COMPANION_POOL = ["Rook", "Pip", "Aster", "the fox Elder", "Moss"]
TRANSFORMATIONS = ["kind", "brave", "patient", "generous", "wise"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place != "the valley beneath the singing mountain":
        raise StoryError("This myth only supports the singing mountain valley.")
    return StoryParams(
        place=args.place,
        child=args.child or rng.choice(NAME_POOL),
        companion=args.companion or rng.choice(COMPANION_POOL),
        quest=args.quest or "return a lost mitt to its owner",
        transformation=args.transformation or rng.choice(TRANSFORMATIONS),
    )


def make_world(params: StoryParams) -> World:
    return World(
        place=params.place,
        child=Person(params.child, "child"),
        companion=Person(params.companion, "companion"),
    )


def generate_story(world: World, params: StoryParams) -> None:
    if params.seed is None:
        material = "|".join(
            [
                params.place,
                params.child,
                params.companion,
                params.quest,
                params.transformation,
            ]
        )
        seed = int.from_bytes(
            hashlib.blake2b(material.encode(), digest_size=8).digest(), "big"
        )
    else:
        seed = params.seed

    tale = TALES[seed % len(TALES)]
    opening = OPENINGS[(seed // len(TALES)) % len(OPENINGS)]
    rhyme = RHYMES[(seed // (len(TALES) * len(OPENINGS))) % len(RHYMES)]

    world.quartz_present = True
    world.mitt_found = True
    world.mitt_owner = tale["owner"]
    world.challenge = tale["challenge"]
    world.clue = tale["clue"]
    world.first_attempt = tale["first_attempt"]
    world.resolution = tale["resolution"]
    world.ending_image = tale["ending"]

    world.say(
        f"{opening}, {world.child.name} walked through {params.place} with "
        f"{world.companion.name}. At their feet rested {tale['quartz']} that "
        f"glimmered like a tiny moon."
    )
    world.say(
        f"Beside the quartz lay a lonely mitt. \"Someone will be missing this,\" "
        f"{world.child.name} said. \"Then we should help it find its hand,\" "
        f"{world.companion.name} replied."
    )
    world.child.memes["kindness"] += 0.5
    world.say(
        f"They began their quest to {params.quest}. The mountain gave them a "
        f"rhyme: \"{rhyme}\""
    )
    world.say(world.challenge)
    world.say(
        f"At first, {world.child.name} {tale['first_attempt']}. "
        f"\"The loudest path is not always the safest,\" said {world.companion.name}."
    )
    world.say(tale["clue"])
    world.say(
        f"\"Let us try what the clue teaches us,\" {world.child.name} answered. "
        f"{tale['action']}"
    )
    world.kindness_shown = True
    world.rhyme_awakened = True
    world.child.meters["energy"] -= 0.25
    world.child.meters["warmth"] += 0.5
    world.child.memes["courage"] += 0.75
    world.child.memes["kindness"] += 1.0
    world.say(tale["resolution"])
    world.say(
        f"Then the quartz began to hum. The mountain repeated, "
        f"\"{tale['lesson']}\""
    )
    world.say(
        f"{world.child.name} understood that being {params.transformation} "
        f"meant noticing another person's need and choosing a safe way to help."
    )
    world.child.memes["wonder"] += 1.0
    world.say(tale["ending"])


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"What did {p.child} find beside the quartz?",
            answer=f"{p.child} found a lost mitt beside the quartz.",
        ),
        QAItem(
            question="Whose mitt was it?",
            answer=f"The mitt belonged to {world.mitt_owner}.",
        ),
        QAItem(
            question=f"What danger changed {p.child}'s first plan?",
            answer=world.challenge,
        ),
        QAItem(
            question="What clue helped the travelers?",
            answer=world.clue,
        ),
        QAItem(
            question=f"How did {p.child} show kindness?",
            answer=world.resolution,
        ),
        QAItem(
            question="What did the quartz and mountain do at the end?",
            answer=world.ending_image,
        ),
        QAItem(
            question=f"What did {p.child} learn?",
            answer=(
                f"{p.child} learned that being {p.transformation} means noticing "
                "another person's need and choosing a careful way to help."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is quartz?",
            answer="Quartz is a hard mineral that can form clear or sparkling crystals.",
        ),
        QAItem(
            question="What is a mitt?",
            answer="A mitt is a warm covering for a hand, usually with one section for the fingers and another for the thumb.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern in which words have matching or similar ending sounds.",
        ),
        QAItem(
            question="Why can dialogue help solve a problem?",
            answer="Dialogue lets characters share observations, ask questions, and change what they decide to do.",
        ),
    ]


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        f"Tell a myth about {params.child} finding quartz and a lost mitt.",
        f"Write a child-friendly myth in which dialogue and rhyme guide {params.child} toward kindness.",
        f"Show how returning a mitt transforms {params.child} into a more {params.transformation} person.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
place(valley).
object(quartz).
object(mitt).
feature(rhyme).
feature(dialogue).
feature(kindness).
quest(return_mitt).
valid_story :-
    place(valley),
    object(quartz),
    object(mitt),
    feature(rhyme),
    feature(dialogue),
    feature(kindness),
    quest(return_mitt).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "valley"),
            asp.fact("object", "quartz"),
            asp.fact("object", "mitt"),
            asp.fact("feature", "rhyme"),
            asp.fact("feature", "dialogue"),
            asp.fact("feature", "kindness"),
            asp.fact("quest", "return_mitt"),
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
    if not any(sym.name == "valid_story" for sym in model):
        print("MISMATCH: ASP story gate did not produce a model.")
        return 1

    sample = generate(
        StoryParams(
            child="Luna",
            companion="Rook",
            quest="return a lost mitt to its owner",
            transformation="kind",
            seed=7,
        )
    )
    required = ("quartz", "mitt", "rhyme", "said", "kindness")
    text = (sample.story + " " + " ".join(q.answer for q in sample.story_qa)).lower()
    missing = [word for word in required if word not in text]
    if missing:
        print("MISMATCH: generated story is missing " + ", ".join(missing))
        return 1

    print("OK: ASP parity and generated-story checks passed.")
    return 0


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
                "quartz_present": world.quartz_present,
                "mitt_found": world.mitt_found,
                "mitt_owner": world.mitt_owner,
                "rhyme_awakened": world.rhyme_awakened,
                "kindness_shown": world.kindness_shown,
            }
        )
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        child="Luna",
        companion="Rook",
        quest="return a lost mitt to its owner",
        transformation="kind",
        seed=11,
    ),
    StoryParams(
        child="Mira",
        companion="Aster",
        quest="return a lost mitt to its owner",
        transformation="patient",
        seed=19,
    ),
    StoryParams(
        child="Orin",
        companion="Pip",
        quest="return a lost mitt to its owner",
        transformation="generous",
        seed=29,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())

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
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
