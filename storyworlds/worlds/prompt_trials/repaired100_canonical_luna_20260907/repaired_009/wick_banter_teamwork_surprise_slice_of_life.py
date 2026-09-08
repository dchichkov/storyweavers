#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a wick, friendly banter, teamwork, and a
surprising little discovery. The story changes as Mara and Jo test a candle,
listen to one another, and solve an ordinary problem together.
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
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Task:
    id: str
    problem: str
    danger: str
    clue: str
    plan: str
    result: str
    surprise: str
    cause_answer: str
    action_answer: str


@dataclass
class Setting:
    id: str
    place: str
    light: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


SETTINGS = {
    "kitchen": Setting("kitchen", "the little kitchen", "warm"),
    "hallway": Setting("hallway", "the narrow hallway", "dim"),
    "balcony": Setting("balcony", "the apartment balcony", "dusky"),
}

TASKS = {
    "blackout": Task(
        "blackout",
        "the lights went out just as Mara was frosting a birthday cake",
        "a loose wick could make the emergency candle sputter beside the paper decorations",
        "the wick leaned to one side and had a dark, soggy tip",
        "trim the wick, set the candle in a saucer, and keep the paper decorations away",
        "the candle gave a steady pool of light while the cake was finished",
        "a tiny moth appeared inside the lampshade when the power returned",
        "The lights went out while Mara was frosting a birthday cake.",
        "They trimmed the wick, put the candle in a saucer, and moved the paper decorations away.",
    ),
    "late_tea": Task(
        "late_tea",
        "Jo wanted tea after a long day, but the kettle would not turn on",
        "a crooked wick could smoke up the room while they searched for a match",
        "the wick was buried under a lump of cooled wax",
        "warm the wax with a spoon, straighten the wick, and use the candle only as a little lamp",
        "they found the tea tin by its label and shared the last biscuits",
        "the tea tin held a note from a neighbor inviting them upstairs",
        "Jo wanted tea after a long day, but the kettle would not turn on.",
        "They cleared and straightened the wick, then used the candle safely as a lamp.",
    ),
    "missing_button": Task(
        "missing_button",
        "Mara had lost a blue button while mending a coat",
        "a weak wick would leave dark corners where the tiny button might hide",
        "a faint shine showed beneath the sofa",
        "trim the wick, carry the candle in a jar, and search from opposite sides",
        "they found the button beside a small wooden spinning top",
        "the spinning top belonged to Jo's grandfather and had been missing for years",
        "Mara lost a blue button while mending a coat.",
        "They made the candle steady, carried it in a jar, and searched from opposite sides.",
    ),
    "plant_check": Task(
        "plant_check",
        "the balcony plants needed checking before a cool evening",
        "an unsteady flame could singe the dry leaves",
        "the wick was too long and made the flame jump",
        "snip the wick, leave the candle on the floor, and inspect the plants with a flashlight",
        "they noticed one tomato had ripened behind the leaves",
        "the tomato was the first one they had grown from a seed",
        "The balcony plants needed checking before a cool evening.",
        "They shortened the wick and kept the candle away while using a flashlight.",
    ),
}

NAMES = ["Mara", "Jo", "Nell", "Sam", "Tavi"]
TRAITS = ["patient", "cheerful", "curious", "careful", "chatty"]

ASP_RULES = r"""
safe_wick(W) :- wick(W), trimmed(W), stable(W), away_from_paper(W).
team_plan(T) :- task(T), safe_wick(wick).
valid_story(T) :- task(T), team_plan(T).
"""


@dataclass
class StoryParams:
    place: str
    task: str
    first_name: str
    second_name: str
    trait: str
    opening: int = 0
    banter: int = 0
    ending: int = 0
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp

    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    lines.extend(
        [
            asp.fact("wick", "wick"),
            asp.fact("trimmed", "wick"),
            asp.fact("stable", "wick"),
            asp.fact("away_from_paper", "wick"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, tid) for sid in SETTINGS for tid in TASKS]


def _choice(value: Optional[str], pool: list[str], rng: random.Random) -> str:
    return value if value in pool else rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = _choice(args.place, list(SETTINGS), rng)
    task = _choice(args.task, list(TASKS), rng)
    first = args.first_name or rng.choice(NAMES)
    remaining = [n for n in NAMES if n != first]
    second = args.second_name or rng.choice(remaining)
    if first == second:
        raise StoryError("first_name and second_name must be different.")
    return StoryParams(
        place=place,
        task=task,
        first_name=first,
        second_name=second,
        trait=args.trait or rng.choice(TRAITS),
        opening=rng.randrange(4),
        banter=rng.randrange(4),
        ending=rng.randrange(4),
    )


def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.task not in TASKS:
        raise StoryError(f"Unknown task: {params.task}")
    if params.first_name == params.second_name:
        raise StoryError("The two teammates need different names.")

    setting = SETTINGS[params.place]
    task = TASKS[params.task]
    world = World(setting)
    first = world.add(
        Entity(
            params.first_name,
            params.first_name,
            "person",
            memes={"confidence": 0.5, "worry": 0.0, "warmth": 0.0},
        )
    )
    second = world.add(
        Entity(
            params.second_name,
            params.second_name,
            "person",
            memes={"confidence": 0.4, "worry": 0.0, "warmth": 0.0},
        )
    )
    wick = world.add(
        Entity(
            "wick",
            "the candle wick",
            "object",
            meters={"length": 1.0, "stability": 0.2, "smoke": 0.0},
        )
    )
    candle = world.add(
        Entity(
            "candle",
            "the candle",
            "object",
            meters={"light": 0.0, "heat": 0.0},
        )
    )

    world.facts.update(first=first, second=second, wick=wick, candle=candle, task=task)

    openings = [
        f"{first.label} and {second.label} were doing an ordinary job in {setting.place}. {first.label} was the {params.trait} one, and {second.label} kept making jokes while they worked.",
        f"In {setting.place}, {first.label} set a candle on the table. {second.label} leaned over it and said, \"That wick looks like it has had a very long day.\"",
        f"The evening had become {setting.light} in {setting.place}. {first.label} brought the candle, and {second.label} brought a saucer, a flashlight, and excellent banter.",
        f"{first.label} had planned a quick task in {setting.place}, but small jobs rarely stayed small. {second.label} arrived just in time to help.",
    ]
    world.say(openings[params.opening % len(openings)])

    world.para()
    world.say(f"Then {task.problem.capitalize()}.")
    world.say(f"The wick was part of the trouble: {task.clue}.")
    first.memes["worry"] += 1
    second.memes["worry"] += 1

    banter = [
        f'"I can fix the wick," said {first.label}. "You can supervise the flame."',
        f'"Should I give the wick a tiny speech?" asked {second.label}. "{first.label}, it looks unconvinced."',
        f'"One thing at a time," said {first.label}. {second.label} nodded. "Good. I only brought three things at a time."',
        f'"What do you see?" asked {first.label}. "A problem," said {second.label}, "and possibly a snack break."',
    ]
    world.say(banter[params.banter % len(banter)])
    world.say(f"{first.label} listened when {second.label} pointed out that {task.danger}.")
    world.para()

    world.say(f"They worked as a team: {task.plan}.")
    wick.meters["length"] = 0.45
    wick.meters["stability"] = 1.0
    wick.meters["smoke"] = 0.0
    candle.meters["light"] = 1.0
    candle.meters["heat"] = 0.3
    first.memes["confidence"] += 0.5
    second.memes["confidence"] += 0.5
    first.memes["warmth"] += 1
    second.memes["warmth"] += 1
    world.say(f"{second.label} held the saucer while {first.label} adjusted the wick. When they stepped back, {task.result.capitalize()}.")
    world.para()

    endings = [
        f"Just then, {task.surprise}. {first.label} and {second.label} laughed, because their small job had found them an unexpected story.",
        f"When the room grew bright again, {task.surprise}. {second.label} called it a bonus, and {first.label} called it a very good reason to keep looking carefully.",
        f"The candle was no longer needed, but {task.surprise}. They left the wick neat and the new discovery on the table between them.",
        f"By the time they finished, {task.surprise}. The ordinary evening felt a little larger than it had before.",
    ]
    world.say(endings[params.ending % len(endings)])
    return world


def prompts(world: World) -> list[str]:
    task: Task = world.facts["task"]  # type: ignore[assignment]
    first: Entity = world.facts["first"]  # type: ignore[assignment]
    second: Entity = world.facts["second"]  # type: ignore[assignment]
    return [
        f"Write a slice-of-life story about {first.label} and {second.label} solving this problem: {task.problem}.",
        f"Tell a gentle teamwork story involving a candle wick, friendly banter, and an unexpected discovery.",
        f"Write an everyday story where two friends listen to each other and make a wick safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    task: Task = world.facts["task"]  # type: ignore[assignment]
    first: Entity = world.facts["first"]  # type: ignore[assignment]
    second: Entity = world.facts["second"]  # type: ignore[assignment]
    return [
        QAItem("What problem did the two friends face?", task.cause_answer),
        QAItem(
            f"Why did {first.label} and {second.label} pay attention to the wick?",
            f"They paid attention because {task.danger}.",
        ),
        QAItem("How did the friends use teamwork?", task.action_answer),
        QAItem("What surprise did they discover?", f"They discovered that {task.surprise}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a wick?",
            "A wick is a strand of material that carries fuel to a candle flame.",
        ),
        QAItem(
            "Why should a candle wick be trimmed?",
            "A trimmed wick usually helps a candle burn with a steadier, smaller flame and less smoke.",
        ),
        QAItem(
            "What does teamwork mean?",
            "Teamwork means people share ideas and actions so they can solve something together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== world qa =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A wick, banter, teamwork, and surprise slice-of-life storyworld."
    )
    parser.add_argument("--place", choices=list(SETTINGS))
    parser.add_argument("--task", choices=list(TASKS))
    parser.add_argument("--first-name")
    parser.add_argument("--second-name")
    parser.add_argument("--trait", choices=TRAITS)
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


def asp_verify() -> int:
    import asp

    python_pairs = {task for _, task in valid_combos()}
    model = asp.one_model(asp_program())
    asp_tasks = {row[0] for row in asp.atoms(model, "valid_story")}
    if python_pairs == asp_tasks:
        print(f"OK: ASP and Python agree on {len(python_pairs)} valid tasks.")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only Python:", sorted(python_pairs - asp_tasks))
    print("Only ASP:", sorted(asp_tasks - python_pairs))
    return 1


CURATED = [
    StoryParams("kitchen", "blackout", "Mara", "Jo", "patient"),
    StoryParams("hallway", "missing_button", "Nell", "Sam", "curious", 1, 1, 1),
    StoryParams("balcony", "plant_check", "Tavi", "Mara", "careful", 2, 2, 2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program())
        return

    if args.verify:
        result = asp_verify()
        if result:
            sys.exit(result)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or len(sample.story.split()) < 50:
                raise StoryError("Verification found an incomplete generated story.")
            if not any('"' in line for line in sample.story.splitlines()):
                raise StoryError("Verification found no spoken dialogue.")
        print("OK: generated stories include dialogue and complete endings.")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

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
