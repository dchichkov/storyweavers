#!/usr/bin/env python3
"""
A small child-facing ghost story world about a quiz, a quiet warning, and a
kind answer that changes a spooky night.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Quiz:
    title: str
    question: str
    answer: str
    clue: str
    lesson: str


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


@dataclass
class StoryParams:
    setting: str
    name: str
    helper: str
    quiz: str
    seed: Optional[int] = None


SETTINGS = {
    "moonlit_schoolhouse": "the old schoolhouse at the edge of town",
}

QUIZZES = {
    "lantern": Quiz(
        title="The Lantern Quiz",
        question="What should you do when a friend is lost in the dark?",
        answer="Stay calm, make a clear light, and call for help.",
        clue="a pale glow blinked three times beside the locked lantern cupboard",
        lesson="a calm light and a helping voice can guide someone home",
    ),
    "owl": Quiz(
        title="The Owl Quiz",
        question="What sound tells you to stop and listen?",
        answer="A soft repeated hoot can be a warning to pause and look around.",
        clue="three quiet hoots came from the empty bell tower",
        lesson="careful listening can reveal a warning before trouble grows",
    ),
    "footprints": Quiz(
        title="The Footprint Quiz",
        question="What should you check before following strange footprints?",
        answer="Check where they begin and end, and ask a trusted helper.",
        clue="small wet footprints stopped neatly before the classroom door",
        lesson="a clue is safer when you study it with someone you trust",
    ),
}

NAMES = ["Luna", "Milo", "Nia", "Theo"]
HELPERS = ["Aunt Bea", "Mr. Rowan", "Grandma June", "Coach Eli"]


def validate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.quiz not in QUIZZES:
        raise StoryError(f"Unknown quiz: {params.quiz}")
    if not params.name.strip() or not params.helper.strip():
        raise StoryError("The child and helper need names.")
    if params.name == params.helper:
        raise StoryError("The child and helper must be different characters.")


def build_world(params: StoryParams) -> World:
    validate(params)
    quiz = QUIZZES[params.quiz]
    world = World(SETTINGS[params.setting])
    child = world.add(Entity("child", "character", params.name))
    helper = world.add(Entity("helper", "character", params.helper))
    ghost = world.add(Entity("ghost", "spirit", "the little ghost"))
    quiz_entity = world.add(Entity("quiz", "quiz", quiz.title))

    child.meters["bravery"] = 1.0
    child.memes["curiosity"] = 1.0
    helper.meters["kindness"] = 1.0
    ghost.meters["loneliness"] = 1.0
    quiz_entity.meters["importance"] = 1.0

    world.facts.update(
        child=child,
        helper=helper,
        ghost=ghost,
        quiz=quiz,
        answer=quiz.answer,
        clue=quiz.clue,
    )

    world.say(
        f"On quiz night, {params.name} carried a pencil into {world.place}. "
        f"The old room smelled of chalk, rain, and dusty books. "
        f"{params.helper} had promised to wait by the door."
    )
    world.say(
        f"On the blackboard, the first question read: “{quiz.question}” "
        f"Before {params.name} could write, a cold little breeze curled around the desk."
    )
    world.say(
        f"Then {quiz.clue}. "
        f"It was a strange clue, because the cupboard had been locked since the schoolhouse closed."
    )
    world.say(
        f"“Did you hear that?” asked {params.name}. "
        f"“I did,” said {params.helper}. “We will look together, and we will not rush.”"
    )
    world.say(
        f"A small gray ghost rose beside the teacher’s desk. "
        f"It held no lantern, and its eyes were as worried as two drops of rain."
    )
    world.say(
        f"“I cannot find the way to my room,” whispered the ghost. "
        f"“The quiz has the answer,” said {params.helper}. "
        f"{params.name} read the question again and wrote, “{quiz.answer}”"
    )
    world.say(
        f"The ghost pointed toward the cupboard. Inside was a little lantern with a broken wick. "
        f"{params.name} did not grab it. Instead, {params.name} called for the caretaker and held up a clear light from the doorway."
    )
    world.say(
        f"The ghost followed the light through the hall and faded beside a door marked Room Three. "
        f"A tiny silver bell rang once, though nobody touched it."
    )
    world.say(
        f"“You solved more than a quiz,” said {params.helper}. "
        f"“You noticed the warning and helped someone who was lost.” "
        f"{params.name} smiled as the blackboard changed its final line to: {quiz.lesson}."
    )
    world.say(
        f"By morning, the schoolhouse was ordinary again. "
        f"Only three pale chalk marks remained beside the quiz answer, like footprints leading safely home."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    quiz: Quiz = world.facts["quiz"]
    child: Entity = world.facts["child"]
    return [
        f"Write a gentle ghost story about {child.label} taking {quiz.title}.",
        f"Foreshadow the ghost with this clue: {quiz.clue}.",
        f"End with the ghost becoming safe after the answer: {quiz.answer}",
    ]


def story_questions(world: World) -> list[QAItem]:
    quiz: Quiz = world.facts["quiz"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            "What quiz question helped solve the ghost's problem?",
            f'The quiz asked, “{quiz.question}” The answer was: “{quiz.answer}”',
        ),
        QAItem(
            "What clue foreshadowed that a ghost needed help?",
            f"{quiz.clue}. It hinted that someone was waiting near the locked cupboard.",
        ),
        QAItem(
            f"How did {child.label} and {helper.label} help?",
            f"They stayed together, used a clear light, and called for help instead of rushing into the dark.",
        ),
        QAItem(
            "What changed at the end?",
            "The ghost found Room Three and faded peacefully, while the quiz gained a final lesson about helping someone who is lost.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        "What is foreshadowing?",
        "Foreshadowing is a clue placed earlier in a story that hints at something important later.",
    ),
    QAItem(
        "Why is a lantern useful in a ghost story?",
        "A lantern makes a dark place easier to see and can help a frightened or lost person find the way.",
    ),
]


def world_questions(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
        world=world,
    )


def valid_combos() -> list[tuple[str, str]]:
    return [(setting, quiz) for setting in SETTINGS for quiz in QUIZZES]


ASP_RULES = r"""
valid(S,Q) :- setting(S), quiz(Q), supports(S,Q).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
        for quiz in QUIZZES:
            lines.append(asp.fact("supports", setting, quiz))
    for quiz in QUIZZES:
        lines.append(asp.fact("quiz", quiz))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        python_combos = set(valid_combos())
        asp_combos = set(asp_valid_combos())
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 0
    if python_combos != asp_combos:
        print("ASP/Python mismatch.")
        print("Python only:", sorted(python_combos - asp_combos))
        print("ASP only:", sorted(asp_combos - python_combos))
        return 1
    for params in CURATED:
        sample = generate(params)
        if "ghost" not in sample.story.lower() or "quiz" not in sample.story.lower():
            return 1
    print(f"OK: ASP/Python parity verified for {len(python_combos)} combinations.")
    return 0


CURATED = [
    StoryParams("moonlit_schoolhouse", "Luna", "Aunt Bea", "lantern", 0),
    StoryParams("moonlit_schoolhouse", "Milo", "Mr. Rowan", "owl", 1),
    StoryParams("moonlit_schoolhouse", "Nia", "Grandma June", "footprints", 2),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle quiz foreshadowing ghost-story world."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--quiz", choices=QUIZZES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "moonlit_schoolhouse"
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != name])
    quiz = args.quiz or rng.choice(list(QUIZZES))
    return StoryParams(setting, name, helper, quiz, args.seed)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            combos = asp_valid_combos()
        except ImportError as exc:
            print(f"ASP unavailable: {exc}")
            return
        print(f"{len(combos)} compatible combinations:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
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
