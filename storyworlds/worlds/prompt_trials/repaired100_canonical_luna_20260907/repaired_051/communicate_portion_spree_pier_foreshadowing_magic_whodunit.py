#!/usr/bin/env python3
"""
A small whodunit storyworld on a magical pier.

The story follows a missing portion of moonlight from a lantern during a
harbor festival spree. Characters must communicate clearly, notice magical
foreshadowing, and discover who moved the light and why.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    location: str = "pier"
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "distance": 0.0,
            "brightness": 0.0,
            "portion": 0.0,
            "certainty": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "curiosity": 0.0,
            "trust": 0.0,
            "courage": 0.0,
            "relief": 0.0,
            "joy": 0.0,
        }
    )


@dataclass
class Setting:
    place: str = "the Lantern Pier"


@dataclass
class StoryParams:
    detective: str
    detective_type: str
    helper: str
    helper_type: str
    keeper: str
    suspect: str
    magical_object: str
    case_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


CASES = [
    {
        "title": "The Case of the Missing Moonbeam",
        "portion": "a silver portion of moonlight",
        "object": "the Moonbell Lantern",
        "clue": "three damp star-shaped footprints",
        "foreshadowing": "the lantern chimed whenever a wave touched the third piling",
        "suspect_action": "a shadow slipped beneath the pier",
        "reveal": "the lighthouse seal had cracked, and the moonlight had floated into a tide pool",
        "solution": "They followed the chiming waves, found the moonlight resting in the tide pool, and guided it back with a shell mirror.",
        "image": "the restored lantern painted a bright silver road across the water",
    },
    {
        "title": "The Mystery of the Vanishing Glow",
        "portion": "one warm portion of enchanted glow",
        "object": "the Harbor Hush Lamp",
        "clue": "a thread of blue ribbon caught on a nail",
        "foreshadowing": "small sparks gathered wherever someone spoke a kind word",
        "suspect_action": "a tiny bell rang inside an empty basket",
        "reveal": "the glow had followed the ribbon to a frightened seal pup hiding beneath the pier",
        "solution": "They communicated gently, used the blue ribbon as a path, and led the glow back without frightening the seal.",
        "image": "the lamp shone softly while the seal pup clapped its flippers",
    },
    {
        "title": "The Riddle of the Stolen Star",
        "portion": "the last bright portion of a bottled star",
        "object": "the Starkeeper's Compass",
        "clue": "a trail of glitter pointed away from the festival table",
        "foreshadowing": "the compass needle kept turning toward a stack of empty nets",
        "suspect_action": "someone whistled the same three notes from behind the fish crates",
        "reveal": "the star had rolled into a net and was lighting a lost crab's way home",
        "solution": "They shared what they knew, lifted the net together, and returned the star after the crab reached its rock.",
        "image": "the star glowed above the pier like a tiny friendly lighthouse",
    },
]


OPENINGS = [
    "At dusk, while gulls folded their wings",
    "Just before the pier festival began",
    "When the tide curled beneath the boards",
    "As colored flags snapped above the harbor",
    "On the evening of the great pier spree",
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A magical whodunit on the Lantern Pier."
    )
    parser.add_argument("--detective")
    parser.add_argument("--type")
    parser.add_argument("--helper")
    parser.add_argument("--helper-type")
    parser.add_argument("--keeper")
    parser.add_argument("--suspect")
    parser.add_argument("--object")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        detective=args.detective or rng.choice(["Luna", "Mara", "Pip", "Theo"]),
        detective_type=args.type or rng.choice(["otter", "cat", "fox", "mouse"]),
        helper=args.helper or rng.choice(["Nell", "Bram", "Ivy", "Sol"]),
        helper_type=args.helper_type or rng.choice(["tern", "seal", "crab", "rabbit"]),
        keeper=args.keeper or rng.choice(["Captain Vale", "Old Mira", "Keeper Jo"]),
        suspect=args.suspect or rng.choice(["the net maker", "the bell ringer", "the lantern painter"]),
        magical_object=args.object or rng.choice(
            ["Moonbell Lantern", "Harbor Hush Lamp", "Starkeeper's Compass"]
        ),
        case_index=rng.randrange(len(CASES)),
        detail_variant=rng.randrange(10000),
    )


def tell(params: StoryParams) -> World:
    if params.detective == params.helper:
        raise StoryError("The detective and helper must have different names.")
    if not params.detective.strip() or not params.helper.strip():
        raise StoryError("Detective and helper names cannot be empty.")

    case = CASES[params.case_index % len(CASES)]
    setting = Setting()
    world = World(setting)

    detective = world.add(
        Entity(
            id="detective",
            kind="animal",
            type=params.detective_type,
            label=params.detective,
            location="pier",
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="animal",
            type=params.helper_type,
            label=params.helper,
            location="pier",
        )
    )
    keeper = world.add(
        Entity(
            id="keeper",
            kind="person",
            type="harbor keeper",
            label=params.keeper,
            location="pier",
        )
    )
    suspect = world.add(
        Entity(
            id="suspect",
            kind="person",
            type="visitor",
            label=params.suspect,
            location="festival table",
        )
    )
    lantern = world.add(
        Entity(
            id="lantern",
            kind="magic",
            type="enchanted lantern",
            label=case["object"],
            owner="keeper",
            location="pier",
        )
    )

    world.facts.update(
        detective=detective,
        helper=helper,
        keeper=keeper,
        suspect=suspect,
        lantern=lantern,
        case=case,
    )

    detective.memes["curiosity"] = 1.0
    helper.memes["trust"] = 1.0
    lantern.meters["brightness"] = 0.5
    lantern.meters["portion"] = 0.5

    opening = OPENINGS[params.detail_variant % len(OPENINGS)]
    world.say(
        f"{opening}, {detective.label} the {detective.type} arrived at {setting.place} "
        f"with {helper.label} the {helper.type}."
    )
    world.say(
        f"The pier was ready for a cheerful spree, but {keeper.label} hurried over "
        f"with a worried face."
    )
    world.say(
        f'"A portion of magic is missing from the {lantern.label}," {keeper.label} said. '
        f'"Please help me discover where it went before the lantern goes dark."'
    )
    world.para()

    detective.memes["worry"] = 1.0
    lantern.meters["certainty"] = 0.2
    world.say(
        f"{detective.label} examined the boards. The case was called "
        f"{case['title']}, and the first clue was {case['clue']}."
    )
    world.say(
        f"{helper.label} pointed toward {params.suspect}. "
        f'"I saw {case["suspect_action"]}," {helper.label} whispered.'
    )
    world.say(
        f'"We should communicate before we accuse anyone," {detective.label} replied. '
        f'"A mystery needs facts, not guesses."'
    )
    world.para()

    detective.memes["courage"] = 1.0
    helper.memes["courage"] = 1.0
    lantern.meters["certainty"] = 0.5
    world.say(
        f"They asked {params.suspect} what had happened. "
        f'"I carried a basket past the lantern, but I did not take its magic," '
        f"{params.suspect} answered. "
        f'"I heard {case["foreshadowing"]}."'
    )
    world.say(
        f"That was important foreshadowing. {detective.label} and {helper.label} "
        f"watched the waves instead of chasing the first suspicion."
    )
    world.say(
        f"{helper.label} said, \"Look! The clues are pointing beneath the pier.\" "
        f"{detective.label} answered, \"Then we will follow them together.\""
    )
    world.para()

    lantern.meters["brightness"] = 1.0
    lantern.meters["portion"] = 1.0
    lantern.meters["certainty"] = 1.0
    detective.memes["relief"] = 1.0
    helper.memes["joy"] = 1.0
    keeper.memes["relief"] = 1.0
    world.say(f"The mystery was solved: {case['reveal']}.")
    world.say(case["solution"])
    world.say(
        f'{keeper.label} smiled. "You communicated, listened, and noticed the magic '
        f'before making a choice," the keeper said.'
    )
    world.para()

    world.say(
        f"{detective.label} learned that a quiet clue can speak loudly when friends "
        f"share what they know."
    )
    world.say(f"At last, {case['image']}.")
    world.log(f"case={params.case_index % len(CASES)}")
    world.log("missing_portion=recovered")
    world.log("suspect=cleared")
    world.log("magic=restored")
    return world


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    detective: Entity = world.facts["detective"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly whodunit about {detective.label} solving a magical mystery on a pier.",
        f"Include {detective.label} and {helper.label} as friends who communicate before accusing anyone.",
        f"Make the missing portion of magic, a foreshadowing clue, and the final discovery important.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    detective: Entity = world.facts["detective"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    keeper: Entity = world.facts["keeper"]  # type: ignore[assignment]
    suspect: Entity = world.facts["suspect"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What mystery did {keeper.label} ask {detective.label} to solve?",
            answer=(
                f"{keeper.label} asked {detective.label} to find the missing "
                f"{case['portion']} from the magical lantern before it went dark."
            ),
        ),
        QAItem(
            question=f"Why did {detective.label} avoid blaming {suspect.label} right away?",
            answer=(
                f"{detective.label} avoided blaming {suspect.label} because a good "
                f"whodunit needs facts, and the friends wanted to communicate and "
                f"check the clues first."
            ),
        ),
        QAItem(
            question="What foreshadowing clue helped solve the case?",
            answer=(
                f"The clue was that {case['foreshadowing']}. It showed the friends "
                f"where to look for the missing magic."
            ),
        ),
        QAItem(
            question=f"How did {detective.label} and {helper.label} restore the magic?",
            answer=(
                f"They followed the clues beneath the pier, discovered that "
                f"{case['reveal']}, and then {case['solution'].lower()}"
            ),
        ),
        QAItem(
            question="What did the friends learn?",
            answer=(
                "They learned that communicating, listening, and examining quiet "
                "clues can solve a mystery better than making a quick accusation."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pier?",
            answer="A pier is a platform built out over water where people can walk, fish, or wait for boats.",
        ),
        QAItem(
            question="What does it mean to communicate?",
            answer="To communicate means to share thoughts or information by speaking, listening, writing, or using signs.",
        ),
        QAItem(
            question="What is a portion?",
            answer="A portion is one part or share of something larger.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a hint early in a story that prepares readers for something important later.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is an imagined power that can make unusual or wonderful things happen.",
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
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        details = [f"type={entity.type}", f"location={entity.location}"]
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(details))
    lines.extend(world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
entity(detective).
entity(helper).
entity(keeper).
entity(lantern).
entity(portion).

communicated(detective, helper).
noticed_foreshadowing(detective).
found(portion).
restored(portion).
cleared(suspect).

case_solved :-
    communicated(detective, helper),
    noticed_foreshadowing(detective),
    found(portion),
    restored(portion),
    cleared(suspect).

happy_end :- case_solved.

#show case_solved/0.
#show happy_end/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("communicated", "detective", "helper"),
            asp.fact("noticed_foreshadowing", "detective"),
            asp.fact("found", "portion"),
            asp.fact("restored", "portion"),
            asp.fact("cleared", "suspect"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show case_solved/0. #show happy_end/0."))
    atoms = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"case_solved/0", "happy_end/0"}
    if atoms != expected:
        print(f"MISMATCH: {sorted(atoms)} != {sorted(expected)}")
        return 1

    for params in CURATED:
        sample = generate(params)
        if "communicate" not in sample.story.lower():
            print("MISMATCH: generated story lacks communication language")
            return 1
        if "pier" not in sample.story.lower():
            print("MISMATCH: generated story lacks pier setting")
            return 1
    print("OK: ASP parity check passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        detective="Luna",
        detective_type="otter",
        helper="Nell",
        helper_type="tern",
        keeper="Captain Vale",
        suspect="the net maker",
        magical_object="Moonbell Lantern",
        case_index=0,
        detail_variant=3,
    ),
    StoryParams(
        detective="Mara",
        detective_type="cat",
        helper="Bram",
        helper_type="seal",
        keeper="Old Mira",
        suspect="the bell ringer",
        magical_object="Harbor Hush Lamp",
        case_index=1,
        detail_variant=17,
    ),
    StoryParams(
        detective="Pip",
        detective_type="fox",
        helper="Ivy",
        helper_type="crab",
        keeper="Keeper Jo",
        suspect="the lantern painter",
        magical_object="Starkeeper's Compass",
        case_index=2,
        detail_variant=29,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show case_solved/0. #show happy_end/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program("#show case_solved/0. #show happy_end/0.")
        )
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 20, 20):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            attempt += 1
            sample = generate(params)
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
        header = (
            f"### variant {index + 1}"
            if len(samples) > 1 and not args.all
            else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
