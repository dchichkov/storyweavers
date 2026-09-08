#!/usr/bin/env python3
"""
A gentle garden-center whodunit about a flush of color, a harmonica, and a
surprising transformation.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))
_storyworlds = os.path.dirname(os.path.dirname(os.path.dirname(_here)))
if not os.path.exists(os.path.join(_storyworlds, "results.py")):
    _storyworlds = os.path.dirname(_storyworlds)
sys.path.insert(0, _storyworlds)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Case:
    id: str
    missing: str
    clue: str
    wrong_guess: str
    reason: str
    transformation: str
    ending: str


CASES = {
    "blue_flower": Case(
        "blue_flower",
        "the blue flower sign",
        "a tiny blue paint mark on the harmonica case",
        "that the quiet helper had hidden the sign",
        "the sign had blown into a watering cart, and the helper moved it before a wheel could crush it",
        "they painted a stronger sign and tied it safely to the flower bench",
        "the new blue sign shone beside a row of flowers while the harmonica played a bright little tune",
    ),
    "lost_label": Case(
        "lost_label",
        "the label for the moon lilies",
        "a silver thread caught on a pot of lavender",
        "that someone had taken the label for a secret prize",
        "the label had slipped into a basket, and the helper saved it from a flush of watering water",
        "they copied the name onto a waterproof card and placed it beside the lilies",
        "the moon lilies stood beneath their fresh label as the last drops flashed like stars",
    ),
    "green_ribbon": Case(
        "green_ribbon",
        "the green ribbon marking the young trees",
        "a curl of ribbon inside an empty seed packet",
        "that the helper had removed the ribbon to confuse shoppers",
        "the ribbon had fallen near a puddle, and the helper lifted it before it tangled around a cart",
        "they washed the ribbon, trimmed its frayed end, and marked the trees with short safe loops",
        "the young trees wore neat green loops while a harmonica note floated through the garden center",
    ),
    "missing_map": Case(
        "missing_map",
        "the little map to the herb table",
        "muddy fingerprints beside the compost display",
        "that the helper had hidden the map to make customers ask for help",
        "rainwater had soaked the map, so the helper carried it indoors to dry",
        "they drew a new map with bold arrows and covered it with a clear sleeve",
        "the map led every visitor to the herbs, and the garden center felt full of cheerful discovery",
    ),
    "yellow_tag": Case(
        "yellow_tag",
        "the yellow tag on the surprise seed tray",
        "one yellow paper corner beneath a stack of pots",
        "that the helper had taken the tag for a decoration",
        "the tag had blown under the pots during a sudden flush of wind",
        "they fastened the tag with a wooden clip and placed the seed tray under shelter",
        "the yellow tag bobbed above the tray as the mystery became a promise of spring",
    ),
}


@dataclass
class StoryParams:
    case: str
    name: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.history: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


def valid_combos() -> list[tuple[str]]:
    return [(key,) for key in CASES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    case = getattr(args, "case", None) or rng.choice(list(CASES))
    if case not in CASES:
        raise StoryError(f"Unknown case '{case}'. Choose one of: {', '.join(CASES)}.")
    name = getattr(args, "name", None) or rng.choice(["Luna", "Milo", "Tessa", "Nico"])
    helper = getattr(args, "helper", None) or rng.choice(["Pip", "Ari", "June", "Sol"])
    if name == helper:
        raise StoryError("The detective and helper must have different names.")
    return StoryParams(case=case, name=name, helper=helper)


def build_world(params: StoryParams) -> World:
    world = World()
    detective = world.add(Entity("detective", "character", params.name, memes={"curiosity": 1.0}))
    helper = world.add(Entity("helper", "character", params.helper))
    world.add(Entity("harmonica", "instrument", "harmonica", meters={"shiny": 1.0}))
    world.add(Entity("display", "place", "garden display", meters={"order": 1.0}))
    world.facts.update({"detective": detective, "helper": helper, "case": CASES[params.case]})
    return world


def _say(world: World, text: str) -> None:
    world.history.append(text)


def generate(params: StoryParams) -> StorySample:
    if params.case not in CASES:
        raise StoryError(f"Cannot build story: case '{params.case}' is not registered.")
    world = build_world(params)
    detective = world.entities["detective"]
    helper = world.entities["helper"]
    case = CASES[params.case]

    detective.memes["surprise"] = 1.0
    _say(world, f"At the garden center, {params.name} came to hear the morning harmonica song.")
    _say(world, f"A bright flush of color filled the flower tables, but {case.missing} was gone.")

    world.entities["display"].meters["order"] = 0.0
    _say(world, f"That was the mystery to solve. Near the empty place, {case.clue}.")
    _say(world, f"\"I think {params.helper} took it,\" said {params.name}. \"I did not,\" replied {params.helper}. \"Please ask what happened.\"")

    detective.memes["curiosity"] += 1.0
    _say(world, f"{params.name} looked again instead of making a hasty guess. The clue did not fit {case.wrong_guess}.")
    _say(world, f"\"Here is the truth,\" said {params.helper}. \"{case.reason.capitalize()}.\"")

    helper.memes["honesty"] = 1.0
    detective.memes["relief"] = 1.0
    _say(world, f"The answer brought a surprise and changed the whole case. Together, they {case.transformation}.")
    world.entities["display"].meters["order"] = 1.0
    world.entities["harmonica"].memes["celebration"] = 1.0
    _say(world, f"The mystery was solved, and the small repair became a transformation: {case.ending}.")
    _say(world, f"Then {params.name} smiled and said, \"Next time, we will follow every clue before we guess.\" {params.helper} answered, \"And I will bring the harmonica.\"")

    story = " ".join(world.history)
    prompts = [
        "Write a gentle Whodunit at a garden center using the words flush and harmonica.",
        f"Tell a mystery where {params.name} solves a surprising garden-center problem with {params.helper}.",
        "Show how a small repair creates a transformation.",
    ]
    story_qa = [
        QAItem("Where did the mystery happen?", "The mystery happened at a garden center."),
        QAItem("What instrument appeared in the story?", "A harmonica appeared in the story and helped mark the cheerful ending."),
        QAItem("What first guess did the detective make?", f"{params.name} first guessed {case.wrong_guess}."),
        QAItem("What was the real reason?", f"The real reason was that {case.reason}."),
        QAItem("How did the mystery end?", f"They solved it when they {case.transformation}."),
    ]
    world_qa = [
        QAItem("What is a mystery?", "A mystery is a question whose answer must be discovered from clues."),
        QAItem("What is a transformation?", "A transformation is a meaningful change from one state into another."),
        QAItem("Why should someone check evidence before blaming a person?", "Evidence can reveal a kinder and more accurate explanation than a first guess."),
        QAItem("What does flush mean here?", "A flush is a sudden or plentiful flow, such as water, wind, or bright color."),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))


ASP_RULES = r"""
valid(Case) :- case(Case).
solved(Case) :- valid(Case).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("case", key) for key in CASES)


def asp_program(show: str = "#show solved/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    expected = {(key,) for key in CASES}
    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "solved"))
    if actual != expected:
        print(f"ASP mismatch: Python={sorted(expected)} ASP={sorted(actual)}")
        return 1
    for key in CASES:
        sample = generate(StoryParams(key, "Luna", "Pip", 1))
        if "garden center" not in sample.story or "harmonica" not in sample.story:
            print(f"Story exercise failed for {key}")
            return 1
    print(f"OK: ASP parity and {len(CASES)} generated stories verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A garden-center harmonica Whodunit.")
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        for item in sorted(asp.atoms(model, "solved")):
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for key in CASES:
            samples.append(generate(StoryParams(key, args.name or "Luna", args.helper or "Pip", base_seed)))
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
