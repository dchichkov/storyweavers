#!/usr/bin/env python3
"""A child-friendly pirate tale about careful thinking and a transformed linen sail."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Item:
    name: str
    material: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    captain: str = "Luna"
    helper: str = "Pip"
    ship: str = "The Blue Minnow"
    cove: str = "Clever Cove"
    cloth: str = "linen"
    lesson: str = "think before you pull"


@dataclass(frozen=True)
class Trial:
    key: str
    danger: str
    clue: str
    mistake: str
    captain_job: str
    helper_job: str
    repair: str
    transformation: str
    ending: str


@dataclass
class World:
    params: StoryParams
    people: dict[str, Person] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


CAPTAINS = ["Luna", "Mara", "Nell", "Tavi"]
HELPERS = ["Pip", "Finn", "Jo", "Moss"]
SHIPS = ["The Blue Minnow", "The Copper Crab", "The Moonlit Gull", "The Little Comet"]
COVES = ["Clever Cove", "Lantern Bay", "Whispering Inlet", "Pebble Harbor"]
CLOTHES = ["linen", "canvas", "cotton"]
LESSONS = ["think before you pull", "listen before you leap", "check the clue before choosing the course"]

TRIALS = [
    Trial(
        "reef",
        "a jagged reef waited beneath the bright water",
        "the tide left a line of wet seaweed pointing around the rocks",
        "she ordered the tiller hard over without studying the tide",
        "held the ship steady",
        "read the wet seaweed line",
        "They followed the tide's safe curve and eased past the reef.",
        "The torn linen map became a bright signal flag after Luna stitched its missing corner.",
        "the new flag snapped proudly above the deck",
    ),
    Trial(
        "storm",
        "a quick storm rolled across the sea",
        "the gulls flew low toward a quiet patch beyond the dark clouds",
        "she pulled every rope at once and tangled the lines",
        "counted the ropes slowly",
        "watched the gulls and clouds",
        "They loosened the knot, shortened the sail, and steered toward the calm water.",
        "The wet linen sail was folded into a warm little storm cape for the lookout.",
        "the cape fluttered while the clouds sailed away",
    ),
    Trial(
        "cave",
        "a narrow cave swallowed the last sunlight",
        "small shells marked the wall on the side with a gentle current",
        "she rowed toward the loudest echo",
        "held the lantern high",
        "counted the shell marks",
        "They trusted the quiet clue, turned away from the echo, and found the open sea.",
        "The old linen chart was transformed into a lantern shade that made the true path glow.",
        "the lantern shone like a tiny moon on the cabin wall",
    ),
    Trial(
        "sandbar",
        "the ship slid onto a hidden sandbar",
        "the water was deeper beside the floating blue bottle",
        "she pushed from the shallow side without checking the water",
        "tested the sand with a pole",
        "watched the bottle's path",
        "They waited for the rising tide and nudged the ship toward the deeper channel.",
        "The linen rope became a braided handline for safely guiding the boat home.",
        "the new handline curled neatly beside the anchor",
    ),
    Trial(
        "fog",
        "silver fog covered the familiar stars",
        "a bell rang twice from the harbor, then once from the open channel",
        "she sailed toward the first sound she heard",
        "trimmed the sail",
        "listened for the repeating bell pattern",
        "They paused, matched the pattern, and sailed toward the harbor.",
        "The linen sail was painted with a golden sun to guide future crews.",
        "the golden sun gleamed when the fog lifted",
    ),
]

OPENINGS = [
    "At dawn, Captain {captain} polished the brass compass aboard {ship}.",
    "Captain {captain} woke to a salty breeze dancing through {ship}.",
    "Near the quiet edge of {cove}, {captain} prepared {ship} for a treasure hunt.",
]
DIALOGUE = [
    '"A pirate must be bold!" cried {captain}.',
    '"Bold is good, but careful is clever," said {helper}.',
    '"What does the sea tell us?" asked {helper}.',
    '"Let us pause and look," answered {captain}.',
]


def make_world(params: StoryParams) -> World:
    if params.captain == params.helper:
        raise StoryError("captain and helper must be different people")
    world = World(params=params)
    captain = Person(params.captain, "captain")
    helper = Person(params.helper, "deck helper")
    cloth = Item("sail_cloth", params.cloth, owner=params.ship)
    world.people = {captain.name: captain, helper.name: helper}
    world.items = {cloth.name: cloth}
    world.facts.update(captain=captain.name, helper=helper.name, ship=params.ship, cove=params.cove)
    return world


def generate_story_world(params: StoryParams) -> World:
    world = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    trial = rng.choice(TRIALS)

    world.say(random.choice(OPENINGS).format(captain=params.captain, ship=params.ship, cove=params.cove))
    world.say(
        f"{params.captain} and {params.helper} carried a folded {params.cloth} chart, "
        f"hoping it would lead them to a silver shell near {params.cove}."
    )
    world.say("The crew called their careful way of thinking cognitive work: using clues before making a choice.")
    world.para()

    world.say(f"Then {trial.danger}.")
    world.say(random.choice(DIALOGUE).format(captain=params.captain, helper=params.helper))
    world.say(f"{params.captain} hurried because {trial.mistake}.")
    world.say(f"{params.helper} pointed out that {trial.clue}.")
    world.say(random.choice(DIALOGUE).format(captain=params.captain, helper=params.helper))
    world.para()

    world.say(f"{params.captain} {trial.captain_job}, while {params.helper} {trial.helper_job}.")
    world.say(trial.repair)
    world.say(f"They remembered the pirate rule: {params.lesson}.")
    world.say(trial.transformation)
    world.para()

    world.say(f"The danger passed, and {params.captain} thanked {params.helper} for noticing the clue.")
    world.say(f"{params.helper} replied, '"A wise crew lets a good question steer the ship."')
    world.say(f"At sunset, {trial.ending}.")
    world.say(
        f"The silver shell was still waiting, but the best treasure was knowing that courage and "
        f"careful thought belonged on the same deck."
    )

    captain = world.people[params.captain]
    helper = world.people[params.helper]
    captain.memes.update(bravery=1.0, caution=1.0, cognitive=1.0)
    helper.memes.update(observation=1.0, teamwork=1.0)
    world.items["sail_cloth"].meters["useful"] = 1.0
    world.items["sail_cloth"].memes["transformed"] = 1.0
    world.facts.update(
        trial=trial.key,
        danger=trial.danger,
        clue=trial.clue,
        mistake=trial.mistake,
        captain_job=trial.captain_job,
        helper_job=trial.helper_job,
        repair=trial.repair,
        transformation=trial.transformation,
        ending=trial.ending,
        resolved=True,
        cognitive=True,
        linen=params.cloth == "linen",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a child-friendly pirate tale about {p.captain} learning to {p.lesson}.",
        f"Tell a cautionary sea adventure aboard {p.ship} using cognitive clues and {p.cloth}.",
        f"Create a transformation story in which a damaged cloth becomes useful again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p, f = world.params, world.facts
    return [
        QAItem(
            question=f"What danger did {p.captain} and {p.helper} face?",
            answer=f"They faced {f['danger']}. The danger threatened their ship, so they had to slow down and study the sea.",
        ),
        QAItem(
            question="What clue helped the crew choose wisely?",
            answer=f"The helpful clue was that {f['clue']}. It gave the crew evidence instead of a guess.",
        ),
        QAItem(
            question="How did the captain and helper work together?",
            answer=f"{p.captain} {f['captain_job']}, while {p.helper} {f['helper_job']}. Their different jobs made the repair safer.",
        ),
        QAItem(
            question="What changed about the cloth?",
            answer=f"The {p.cloth} cloth was transformed: {f['transformation']}. It became useful in a new way.",
        ),
        QAItem(
            question="What cautionary lesson did the pirates learn?",
            answer=f"They learned to {p.lesson}. Careful thinking helped them turn a risky moment into a safe voyage.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does cognitive mean in this story?",
            answer="Cognitive means related to thinking, noticing, remembering, and making decisions. The crew used cognitive skills when they examined clues before acting.",
        ),
        QAItem(
            question="What is linen?",
            answer="Linen is a strong cloth made from the fibers of the flax plant. It can be used for sails, clothing, maps, or other useful fabric items.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a meaningful change in form or use. In this tale, the cloth became a different helpful object after the danger passed.",
        ),
        QAItem(
            question="Why should a sailor inspect a danger before acting?",
            answer="Inspection can reveal the cause, direction, or safest route through a problem. A clear clue can prevent a hurried choice from making the danger worse.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
captain(C) :- captain_name(C).
helper(H) :- helper_name(H).
cloth(M) :- cloth_material(M).
cognitive_choice(C,H) :- captain(C), helper(H), clue_used(C,H).
safe_voyage(C,H,M) :- cognitive_choice(C,H), transformed_cloth(M).
cautionary_transformation(C,H,M) :- safe_voyage(C,H,M), cloth(M).
"""

DEFAULT_PARAMS = StoryParams()


def asp_facts() -> str:
    import asp
    p = DEFAULT_PARAMS
    return "\n".join(
        [
            asp.fact("captain_name", p.captain),
            asp.fact("helper_name", p.helper),
            asp.fact("cloth_material", p.cloth),
            asp.fact("clue_used", p.captain, p.helper),
            asp.fact("transformed_cloth", p.cloth),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    symbols = asp.one_model(asp_program("#show cautionary_transformation/3."))
    atoms = asp.atoms(symbols, "cautionary_transformation")
    if atoms:
        print("OK: ASP and Python agree on a cautious cloth transformation.")
        return 0
    print("MISMATCH: expected cautionary_transformation atom missing.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--ship", choices=SHIPS)
    parser.add_argument("--cove", choices=COVES)
    parser.add_argument("--cloth", choices=CLOTHES)
    parser.add_argument("--lesson", choices=LESSONS)
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = args.captain or rng.choice(CAPTAINS)
    helper = args.helper or rng.choice([x for x in HELPERS if x != captain])
    return StoryParams(
        seed=args.seed,
        captain=captain,
        helper=helper,
        ship=args.ship or rng.choice(SHIPS),
        cove=args.cove or rng.choice(COVES),
        cloth=args.cloth or "linen",
        lesson=args.lesson or rng.choice(LESSONS),
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        w = sample.world
        print(
            "\n--- trace ---\n"
            f"captain={w.params.captain}\n"
            f"helper={w.params.helper}\n"
            f"trial={w.facts['trial']}\n"
            f"clue={w.facts['clue']}\n"
            f"transformation={w.facts['transformation']}\n"
            f"resolved={w.facts['resolved']}"
        )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show cautionary_transformation/3."))
        return

    if args.verify:
        code = asp_verify()
        if code == 0:
            sample = generate(StoryParams(seed=17))
            if not sample.story or "cognitive" not in sample.story or "linen" not in sample.story:
                print("MISMATCH: generated story failed required narrative checks.")
                code = 1
        raise SystemExit(code)

    if args.asp:
        import asp
        symbols = asp.one_model(asp_program("#show cautionary_transformation/3."))
        for atom in asp.atoms(symbols, "cautionary_transformation"):
            print(f"cautionary_transformation{atom}.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, trial in enumerate(TRIALS):
            params = StoryParams(
                seed=base_seed + index,
                captain=CAPTAINS[index % len(CAPTAINS)],
                helper=HELPERS[index % len(HELPERS)],
                ship=SHIPS[index % len(SHIPS)],
                cove=COVES[index % len(COVES)],
                cloth="linen",
                lesson=LESSONS[index % len(LESSONS)],
            )
            if params.captain == params.helper:
                params.helper = "Pip"
            samples.append(generate(params))
    else:
        if args.n < 1:
            raise SystemExit("-n must be at least 1")
        for index in range(args.n):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
