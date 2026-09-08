#!/usr/bin/env python3
"""
A heartwarming little world about Mooshy, a plum, and a helpful machine.

Seed words: mooshy, machine, plum
Features: Happy Ending, Repetition
Style: Heartwarming
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = [
    "the warm kitchen",
    "the little orchard shed",
    "the village jam room",
    "the sunny market porch",
]
MACHINE_NAMES = ["Merry Press", "Plum Bell", "Kindness Maker", "Sunshine Squeezer"]
HELPERS = ["Grandma Bea", "Pip", "Nell", "Tomo"]
PLUM_COLORS = ["purple", "rosy", "deep red", "violet"]
MOOSHY_WORDS = ["mooshy", "soft and mooshy", "gently squishy", "plump and yielding"]

OPENINGS = [
    "Morning light slipped through the window and painted a golden square on the floor.",
    "The day began with birdsong, warm toast, and one very important plum.",
    "In the quiet little room, every jar waited for a sweet new beginning.",
    "A cheerful bell rang outside, and Mooshy woke with a hopeful smile.",
]

PROBLEMS = [
    {
        "goal": "make one special jar of plum jam for the neighbors",
        "problem": "the machine gave a tiny cough and stopped before the plum could become jam",
        "guess": "the machine was too old to help",
        "clue": "the same brass button blinked three times whenever the handle came loose",
        "truth": "the handle was not broken; it simply needed to be held steady",
        "failed": "pulling the handle harder made the machine wobble and spill a little juice",
        "roles": "one held the bowl, one steadied the handle, and one counted the careful presses",
        "solution": "They cleaned the gears, tightened the handle, and pressed together in a gentle rhythm",
        "ending": "Soon a row of shining jars warmed the table, and every neighbor had a taste",
        "safe": "the special plum jam",
    },
    {
        "goal": "prepare a plum treat for a friend who had been feeling lonely",
        "problem": "the machine hummed but would not turn the plum into a smooth, sweet treat",
        "guess": "the plum was not good enough",
        "clue": "a small bit of leaf was tucked beneath the silver wheel",
        "truth": "the machine needed a clean path, not a better plum",
        "failed": "feeding in another plum only made the wheel squeak louder",
        "roles": "one brushed the leaf away, one held the bowl, and one spoke kindly to the worried machine",
        "solution": "They cleared the wheel, checked the bowl, and tried again with patient hands",
        "ending": "The finished treat was wrapped with a ribbon and carried to the friend before sunset",
        "safe": "the plum treat",
    },
    {
        "goal": "fill small cups for the orchard picnic",
        "problem": "the machine made three little plops and left the plum sitting proudly on top",
        "guess": "the machine had forgotten how to work",
        "clue": "the plum's round side matched a turning mark on the machine's wooden tray",
        "truth": "the plum had been placed sideways instead of on the turning mark",
        "failed": "turning the tray at random sent juice in a bright purple splash",
        "roles": "one wiped the tray, one found the turning mark, and one placed the plum carefully",
        "solution": "They dried the tray, lined up the mark, and repeated the gentle turn until the cups were full",
        "ending": "At the picnic, everyone shared the cups, and the machine wore a clean blue bow",
        "safe": "the picnic cups",
    },
]

REPETITIONS = [
    "Tap, turn, breathe. Tap, turn, breathe.",
    "Together, slowly, kindly. Together, slowly, kindly.",
    "One small step, then one more. One small step, then one more.",
    "Clean, steady, ready. Clean, steady, ready.",
]

LESSONS = [
    "They learned that repeating a careful kindness can make a hard job feel possible.",
    "The friends discovered that patience is not standing still; it is trying gently again.",
    "Mooshy understood that a machine can need care, just as a friend can.",
    "Everyone saw that mistakes become smaller when people face them together.",
]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    warmth: float = 1.0


@dataclass
class Mood:
    worry: float = 0.0
    hope: float = 0.0
    tenderness: float = 0.0


@dataclass
class StoryParams:
    place: str
    mooshy_name: str
    helper_name: str
    machine_name: str
    plum_color: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mood: Mood) -> None:
        self.setting = setting
        self.mood = mood
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(group) for group in self.lines if group)


def tell(params: StoryParams) -> World:
    world = World(Setting(params.place), Mood())
    rng = random.Random(
        params.seed
        if params.seed is not None
        else "|".join(
            [
                params.place,
                params.mooshy_name,
                params.helper_name,
                params.machine_name,
                params.plum_color,
            ]
        )
    )
    problem = rng.choice(PROBLEMS)
    repetition = rng.choice(REPETITIONS)
    opening = rng.choice(OPENINGS)
    lesson = rng.choice(LESSONS)
    mooshy_word = rng.choice(MOOSHY_WORDS)

    mooshy = world.add(
        Entity(
            id=params.mooshy_name,
            kind="character",
            label="a small, soft-hearted friend",
            memes={"hope": 1.0, "care": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper_name,
            kind="character",
            label="a patient helper",
            memes={"care": 1.0, "patience": 1.0},
        )
    )
    machine = world.add(
        Entity(
            id=params.machine_name,
            kind="machine",
            label="a friendly plum machine",
            owner=params.mooshy_name,
            meters={"cleanliness": 0.0, "working": 0.0},
            memes={"trust": 0.0},
        )
    )
    plum = world.add(
        Entity(
            id="plum",
            kind="fruit",
            label=f"a {params.plum_color} plum",
            owner=params.mooshy_name,
            meters={"freshness": 1.0, "whole": 1.0},
            memes={"belonging": 1.0},
        )
    )

    world.mood.worry = 1.0
    world.mood.hope = 1.0
    world.say(opening)
    world.say(
        f"In {params.place}, {params.mooshy_name} kept one {mooshy_word} {params.plum_color} plum beside the {params.machine_name}."
    )
    world.say(
        f"{params.mooshy_name} wanted to {problem['goal']}, because sharing something warm felt like a hug that could be tasted."
    )
    world.para()

    world.say(f"But {problem['problem']}.")
    world.say(
        f"{params.mooshy_name} looked at the silent machine and whispered, “{problem['guess'].capitalize()}.”"
    )
    world.say(
        f'{params.helper_name} came close and said, “Let us listen before we give up.”'
    )
    world.say(
        f'{params.mooshy_name} answered, “I am worried, but I can try one more time.”'
    )
    world.say(f"{problem['failed']}.")
    world.say(
        f"The friends paused and found the important clue: {problem['clue']}."
    )
    world.say(f"{params.helper_name} smiled. “That is something we can fix together.”")
    world.para()

    world.say(repetition)
    world.say(
        f"They {problem['roles']}. The machine gave a soft, hopeful hum."
    )
    world.say(f"{problem['solution']}.")
    world.say(
        f"Each careful repetition made the work steadier: {repetition.lower()}"
    )
    world.say(
        f"{params.mooshy_name} said, “You did not leave me alone with the trouble.”"
    )
    world.say(
        f"{params.helper_name} replied, “And you did not leave the machine without a chance.”"
    )
    world.para()

    world.say(f"{problem['ending']}.")
    world.say(lesson)
    world.say(
        f"When evening came, {params.mooshy_name} placed the first jar beside the now-clean {params.machine_name}, and the machine gave one gentle happy chime."
    )

    world.mood.worry = 0.0
    world.mood.hope = 1.0
    world.mood.tenderness = 1.0
    machine.meters["cleanliness"] = 1.0
    machine.meters["working"] = 1.0
    machine.memes["trust"] = 1.0
    plum.meters["whole"] = 0.0
    plum.meters["freshness"] = 0.0
    mooshy.memes["hope"] = 2.0
    mooshy.memes["belonging"] = 1.0
    helper.memes["patience"] = 2.0

    world.facts.update(
        mooshy=mooshy,
        helper=helper,
        machine=machine,
        plum=plum,
        problem=problem,
        repetition=repetition,
        lesson=lesson,
        mooshy_word=mooshy_word,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    problem = world.facts["problem"]
    return [
        "Write a heartwarming story about Mooshy, a machine, and a plum.",
        f"Show how friends solve a problem while trying to {problem['goal']}.",
        "Repeat a gentle phrase so patience and teamwork feel important.",
    ]


def story_qa(world: World) -> list[QAItem]:
    mooshy = world.facts["mooshy"]
    helper = world.facts["helper"]
    machine = world.facts["machine"]
    problem = world.facts["problem"]
    return [
        QAItem(
            question=f"What did {mooshy.id} want to do with the plum?",
            answer=f"{mooshy.id} wanted to {problem['goal']}, so the plum could become a loving gift or shared treat.",
        ),
        QAItem(
            question=f"Why did the machine stop working at first?",
            answer=f"The friends found that {problem['truth']}. They learned this from the clue that {problem['clue']}.",
        ),
        QAItem(
            question=f"How did {mooshy.id} and {helper.id} repair the problem?",
            answer=f"They worked together: {problem['roles']}. Then {problem['solution']}.",
        ),
        QAItem(
            question=f"What changed for the {machine.id} by the end?",
            answer=f"The machine became clean and worked again. It helped make the finished treat, then gave one gentle happy chime.",
        ),
        QAItem(
            question="What was the heartwarming lesson?",
            answer=world.facts["lesson"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a plum?",
            answer="A plum is a soft, round fruit with smooth skin and a stone inside.",
        ),
        QAItem(
            question="What is a machine?",
            answer="A machine is something made to help with a task when people use it carefully.",
        ),
        QAItem(
            question="Why can repetition help?",
            answer="Repetition can help people learn a rhythm, notice mistakes, and keep trying patiently.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id} ({entity.kind}) {' '.join(details)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming story world about Mooshy, a machine, and a plum."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--mooshy-name", default="Mooshy")
    parser.add_argument("--helper-name", choices=HELPERS)
    parser.add_argument("--machine-name", choices=MACHINE_NAMES)
    parser.add_argument("--plum-color", choices=PLUM_COLORS)
    parser.add_argument("--seed", type=int, default=None)
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
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        mooshy_name=args.mooshy_name,
        helper_name=args.helper_name or rng.choice(HELPERS),
        machine_name=args.machine_name or rng.choice(MACHINE_NAMES),
        plum_color=args.plum_color or rng.choice(PLUM_COLORS),
    )


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    return "\n".join(
        [
            "character(mooshy).",
            "object(machine).",
            "object(plum).",
            "feature(happy_ending).",
            "feature(repetition).",
            "style(heartwarming).",
            "needs_care(machine).",
            "can_be_shared(plum).",
        ]
    )


ASP_RULES = r"""
valid_story :-
    character(mooshy),
    object(machine),
    object(plum),
    feature(happy_ending),
    feature(repetition),
    style(heartwarming),
    needs_care(machine),
    can_be_shared(plum).
#show valid_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/0."))
    values = set(asp.atoms(model, "valid_story"))
    expected = {()}
    if values == expected:
        params = StoryParams(
            place=PLACES[0],
            mooshy_name="Mooshy",
            helper_name=HELPERS[0],
            machine_name=MACHINE_NAMES[0],
            plum_color=PLUM_COLORS[0],
            seed=7,
        )
        sample = generate(params)
        required = ["Mooshy", "machine", "plum"]
        if all(word.lower() in sample.story.lower() for word in required):
            print("OK: ASP facts, Python world, and generated story agree.")
            return 0
        print("MISMATCH: generated story omitted a required seed word")
        return 1
    print("MISMATCH:", values, expected)
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.n < 1:
        raise StoryError("number of stories must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed))
        params.seed = base_seed
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### story {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
