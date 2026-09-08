#!/usr/bin/env python3
"""
A gentle slice-of-life storyworld about a mysterious whosejigger, a small
problem, and the surprise at the end.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=lambda: {"look", "ask", "try", "repair"})


@dataclass
class StoryParams:
    child_name: str
    helper_name: str
    adult_name: str
    object_choice: int = 0
    clue_choice: int = 0
    surprise_choice: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    place: str
    first_view: str
    clue: str
    likely_use: str
    repair: str
    surprise: str
    ending_image: str


CASES = [
    Case(
        "the apartment kitchen",
        "a tiny silver tool beside the fruit bowl",
        "a loose screw on the jam-jar lid",
        "tighten the lid",
        "turned the little wheel until the lid sat snug",
        "the jar opened to reveal a note from breakfast",
        "the note rested under the lid, saying, “Have a bright day!”",
    ),
    Case(
        "the front hall",
        "a bright red tool on the shoe bench",
        "the wobbly hook where the house key usually hung",
        "steady the hook",
        "held the hook straight while the screw went back in",
        "the hidden pocket behind the hook held a lost blue button",
        "the blue button waited in a dish beside the keys",
    ),
    Case(
        "the community garden shed",
        "a wooden-handled tool near the watering cans",
        "a loose latch that let the shed door swing open",
        "fix the latch",
        "slid the small metal piece into its groove",
        "a packet of sunflower seeds had been tucked behind the latch",
        "the seed packet lay beside the watering can in the warm afternoon light",
    ),
    Case(
        "the laundry room",
        "a yellow tool on top of the folded towels",
        "the crooked knob on the soap drawer",
        "straighten the knob",
        "tightened the knob and tested the drawer twice",
        "a missing sock had been hiding behind the drawer",
        "the striped sock joined its pair before the next wash",
    ),
    Case(
        "the little library",
        "a curious tool beside the return basket",
        "a bent label on the shelf marked “Stories”",
        "smooth the label",
        "pressed the label flat and secured its corner",
        "a tiny drawing appeared on the back of the label",
        "the drawing showed a smiling moon above the quiet shelf",
    ),
]

CLUES = [
    "looked first, asked a question, and changed only one thing at a time",
    "placed the nearby pieces in a row before touching the problem",
    "checked the object gently, then tried the simplest repair",
    "asked who had used the object last and listened carefully",
]

SURPRISE_LINES = [
    "At the end, the surprise made the ordinary place feel special.",
    "The surprise was small, but it made everyone stop and smile.",
    "No one had expected that final little discovery.",
    "The problem had led them to something kind and unexpected.",
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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


def build_story(params: StoryParams) -> World:
    if not params.child_name.strip():
        raise StoryError("child_name must not be empty")
    if not params.helper_name.strip():
        raise StoryError("helper_name must not be empty")
    if not params.adult_name.strip():
        raise StoryError("adult_name must not be empty")

    case = CASES[params.object_choice % len(CASES)]
    method = CLUES[params.clue_choice % len(CLUES)]
    surprise_line = SURPRISE_LINES[params.surprise_choice % len(SURPRISE_LINES)]
    world = World(Setting(case.place))

    child = world.add(Entity("Child", "character", "child", params.child_name))
    helper = world.add(Entity("Helper", "character", "child", params.helper_name))
    adult = world.add(Entity("Adult", "character", "adult", params.adult_name))
    tool = world.add(Entity("Whosejigger", "thing", "tool", "the whosejigger"))
    problem = world.add(Entity("Problem", "thing", "problem", "the small problem"))

    world.facts.update(
        child=child,
        helper=helper,
        adult=adult,
        tool=tool,
        problem=problem,
        case=case,
        method=method,
        surprise_line=surprise_line,
    )

    child.memes["curious"] = 1.0
    world.say(
        f"On an ordinary afternoon in {case.place}, {child.label} noticed {case.first_view}. "
        f"It was a whosejigger, though nobody in the room knew what a whosejigger was for."
    )
    world.say(
        f'"Maybe it belongs to something," {child.label} said. {helper.label} leaned closer. '
        f'"Let us find out before we use it."'
    )

    world.para()
    helper.memes["careful"] = 1.0
    world.say(
        f"Just then, {adult.label} came in and pointed to {case.clue}. "
        f"The small problem was making an everyday task difficult."
    )
    world.say(
        f'"Could the whosejigger help?" asked {helper.label}. '
        f'"It might," said {adult.label}, "but solving the problem means understanding it first."'
    )
    world.say(
        f"So {child.label} and {helper.label} {method}. "
        f"They noticed that the whosejigger seemed made for one simple job: {case.likely_use}."
    )
    tool.meters["understood"] = 1.0
    problem.meters["examined"] = 1.0

    world.para()
    child.memes["determined"] = 1.0
    world.say(
        f"{child.label} held {case.clue.split(' on ')[0] if ' on ' in case.clue else 'the nearby piece'} still, "
        f"and {helper.label} used the whosejigger carefully. Together they {case.repair}."
    )
    problem.meters["solved"] = 1.0
    tool.memes["useful"] = 1.0
    world.say(
        f'"It worked!" said {child.label}. "The whosejigger was not strange after all." '
        f'{helper.label} smiled. "It was waiting for the right question."'
    )

    world.para()
    world.say(
        f"Then came the surprise. {case.surprise.capitalize()} {surprise_line}"
    )
    world.say(
        f"{adult.label} thanked them for solving the problem instead of guessing. "
        f"{case.ending_image.capitalize()}."
    )
    world.facts["lesson"] = (
        "Careful questions and small tests can turn a confusing problem into a useful discovery."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    return [
        f"Write a slice-of-life story about {child.label} finding a whosejigger in {world.setting.place}.",
        f"Show {child.label} and a friend solving a small problem by discovering that {case.likely_use} is the whosejigger's job.",
        "End with a gentle surprise that changes how the characters see an ordinary object.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    adult: Entity = world.facts["adult"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Where did {child.label} find the whosejigger?",
            f"{child.label} found the whosejigger in {case.place}, beside {case.first_view.split(' beside ', 1)[-1]}.",
        ),
        QAItem(
            f"How did {child.label} and {helper.label} solve the problem?",
            f"They examined {case.clue}, changed only one thing at a time, and used the whosejigger to {case.likely_use}.",
        ),
        QAItem(
            f"What did {adult.label} teach the children?",
            f"{adult.label} taught them to understand a problem before using a tool and to test a simple solution carefully.",
        ),
        QAItem(
            "What was the surprise at the end?",
            f"The surprise was that {case.surprise}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is problem solving?",
            "Problem solving means understanding what is wrong, trying a sensible action, and checking whether it helped.",
        ),
        QAItem(
            "Why should someone inspect a tool before using it?",
            "Inspecting a tool helps a person learn what it is meant to do and use it safely.",
        ),
        QAItem(
            "What is a surprise?",
            "A surprise is something unexpected that happens or is discovered.",
        ),
        QAItem(
            "Why can a small test be useful?",
            "A small test changes one thing at a time, making it easier to see what caused the result.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:12} ({entity.type:8}) {' '.join(details)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("topic", "whosejigger"),
            asp.fact("topic", "end"),
            asp.fact("feature", "problem_solving"),
            asp.fact("feature", "surprise"),
            asp.fact("style", "slice_of_life"),
            asp.fact("action", "inspect"),
            asp.fact("action", "repair"),
            asp.fact("outcome", "solved"),
        ]
    )


ASP_RULES = r"""
topic(whosejigger).
topic(end).
feature(problem_solving).
feature(surprise).
style(slice_of_life).
action(inspect).
action(repair).
outcome(solved).

story_ok :-
    topic(whosejigger),
    topic(end),
    feature(problem_solving),
    feature(surprise),
    style(slice_of_life),
    action(inspect),
    action(repair),
    outcome(solved).

#show story_ok/0.
"""


def asp_program(show: str = "#show story_ok/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    ok = any(symbol.name == "story_ok" for symbol in model)
    if not ok:
        print("MISMATCH: ASP twin failed.")
        return 1
    rng = random.Random(17)
    for _ in range(5):
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if "whosejigger" not in sample.story or "surprise" not in sample.story.lower():
            print("MISMATCH: generated story lacks required narrative elements.")
            return 1
    print("OK: ASP twin and generated stories agree.")
    return 0


CHILD_NAMES = ["Luna", "Milo", "Nora", "Theo", "Iris", "Sam"]
HELPER_NAMES = ["June", "Ari", "Pip", "Maya", "Owen", "Zoe"]
ADULT_NAMES = ["Mom", "Dad", "Aunt Rae", "Uncle Ben"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a slice-of-life story about a whosejigger, problem solving, and surprise."
    )
    parser.add_argument("--child-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--adult-name")
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
        child_name=args.child_name or rng.choice(CHILD_NAMES),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
        adult_name=args.adult_name or rng.choice(ADULT_NAMES),
        object_choice=rng.randrange(len(CASES)),
        clue_choice=rng.randrange(len(CLUES)),
        surprise_choice=rng.randrange(len(SURPRISE_LINES)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("story_ok" if any(symbol.name == "story_ok" for symbol in model) else "no model")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(CASES)):
            params = StoryParams(
                child_name="Luna",
                helper_name="June",
                adult_name="Mom",
                object_choice=index,
                clue_choice=index % len(CLUES),
                surprise_choice=index % len(SURPRISE_LINES),
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            index += 1
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
