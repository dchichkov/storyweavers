#!/usr/bin/env python3
"""Cautionary animal StoryWorld about slosh, problem solving, and a safe crossing."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import copy
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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


ANIMALS = ["Mara", "Pip", "Tavi", "Nell", "Rook", "Bram", "Lulu", "Otis"]
PLACES = ["the ferny creek bank", "the sunny orchard path", "the mossy pond trail"]
CARRIERS = ["a blue tin pail", "a round wooden tub", "a bright green watering can"]
TASKS = (
    {
        "id": "berries",
        "cargo": "blackberries",
        "destination": "the hedgehogs' picnic stone",
        "problem": "the path dipped sharply beside a patch of loose stones",
        "clue": "small berry leaves floated in the spilled water",
        "fix": "a slow, level route marked with flat leaves",
        "image": "the hedgehogs sharing shiny berries beside a dry pail",
        "lesson": "hurrying with a heavy, sloshing load can turn a small mistake into a bigger mess",
    },
    {
        "id": "seeds",
        "cargo": "sunflower seeds",
        "destination": "the finches' winter shelf",
        "problem": "a fallen branch blocked the straight trail",
        "clue": "the branch had fresh scrape marks from the pail's rim",
        "fix": "a winding route around the branch, cleared one pebble at a time",
        "image": "finches pecking happily from a full shelf while the water stayed inside",
        "lesson": "a safe detour is wiser than forcing a difficult path",
    },
    {
        "id": "flowers",
        "cargo": "water for the thirsty daisies",
        "destination": "the little flower bed",
        "problem": "the ground became muddy beneath a dripping willow",
        "clue": "three round puddles showed exactly where the carrier had tipped",
        "fix": "a board bridge and two resting places",
        "image": "bright daisies lifting their heads beside the steady green can",
        "lesson": "pausing to plan protects both the helper and the thing being carried",
    },
    {
        "id": "apples",
        "cargo": "tiny apples",
        "destination": "the badgers' supper log",
        "problem": "a narrow tunnel made the carrier bump against both walls",
        "clue": "the damp wall carried a fresh blue streak from the tin",
        "fix": "a wider path around the hill",
        "image": "badgers rolling apples into a neat supper basket",
        "lesson": "not every short path is the safest path",
    },
    {
        "id": "clover",
        "cargo": "clover tea",
        "destination": "the old tortoise's shade",
        "problem": "a playful stream crossed the trail and tugged at loose reeds",
        "clue": "the reeds bent downstream before the pail even reached them",
        "fix": "a firm stepping-stone crossing tested with an empty carrier first",
        "image": "the tortoise sipping warm tea under a leaf umbrella",
        "lesson": "testing a plan with less risk can prevent a dangerous surprise",
    },
)


@dataclass
class Entity:
    id: str
    type: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    animal_name: str
    carrier: str
    task_id: str = "berries"
    opening_id: int = 0
    dialogue_id: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

    def copy(self) -> "World":
        return copy.deepcopy(self)


OPENINGS = (
    "One bright morning",
    "After a night of silver rain",
    "When the orchard woke",
    "At the edge of a warm afternoon",
    "Beneath clouds shaped like boats",
    "As birds began their breakfast songs",
)

DIALOGUES = (
    ('"I can carry it quickly," said {name}.', '"Listen to that slosh," warned the helper. "Quickly is not always safely."'),
    ('"The shortest way is through the tunnel," said {name}.', '"The widest way may be wiser," replied the helper. "Let us look before we go."'),
    ('"I will not spill a single drop," promised {name}.', '"Then show the pail a careful path," said the helper. "Feet first, paws second."'),
    ('"This load is easy!" cried {name}.', '"Easy loads can still tip," said the helper. "What will you do when the ground changes?"'),
    ('"I know this trail," said {name}.', '"Knowing the trail is not the same as checking it today," replied the helper.'),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal StoryWorld about slosh, caution, and problem solving."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--animal-name", choices=ANIMALS)
    parser.add_argument("--carrier", choices=CARRIERS)
    parser.add_argument("--task", choices=[task["id"] for task in TASKS])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(
            f"--{flag}", action="store_true", dest=flag.replace("-", "_")
        )
    return parser


def task_for(task_id: str) -> dict:
    for task in TASKS:
        if task["id"] == task_id:
            return task
    raise StoryError(f"Unknown task: {task_id}")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        animal_name=args.animal_name or rng.choice(ANIMALS),
        carrier=args.carrier or rng.choice(CARRIERS),
        task_id=args.task or rng.choice([task["id"] for task in TASKS]),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
    )


def tell(params: StoryParams) -> World:
    task = task_for(params.task_id)
    if not params.animal_name.strip():
        raise StoryError("The animal must have a name.")
    if params.carrier not in CARRIERS:
        raise StoryError("The carrier must be a registered container.")

    world = World(params.place)
    animal = world.add(
        Entity(
            id="animal",
            type="animal",
            label=params.animal_name,
            role="careful courier",
            meters={"balance": 0.35, "energy": 0.85},
            memes={"confidence": 0.75, "caution": 0.25},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            type="animal",
            label="a patient old mouse",
            role="helper",
            meters={"balance": 0.9, "energy": 0.7},
            memes={"wisdom": 1.0, "care": 1.0},
        )
    )
    container = world.add(
        Entity(
            id="carrier",
            type="container",
            label=params.carrier,
            role="water carrier",
            meters={"fullness": 0.9, "stability": 0.45},
            memes={"value": 0.8},
        )
    )
    world.facts.update(
        animal=animal,
        helper=helper,
        carrier=container,
        task=task,
        plan="reckless shortcut",
        resolved=False,
        spill_amount="a few drops",
        final_route="unplanned",
    )

    world.say(
        f"{OPENINGS[params.opening_id]}, {animal.label} filled {params.carrier} with "
        f"water and {task['cargo']} for {task['destination']}."
    )
    world.say(
        f"The load was useful but heavy, and every step made a soft slosh against the sides."
    )
    world.say(
        f"At {params.place}, {helper.label} watched the carrier wobble near "
        f"{task['problem']}."
    )
    world.para()

    first, second = DIALOGUES[params.dialogue_id]
    world.say(first.format(name=animal.label))
    world.say(second)
    world.say(
        f"Still, {animal.label} chose a shortcut. The carrier bumped, water splashed, "
        f"and {task['cargo']} slid toward the rim."
    )
    world.say(
        f"One more jolt would have spilled the whole load before it reached "
        f"{task['destination']}."
    )
    animal.memes["confidence"] = 0.4
    animal.memes["caution"] = 0.5
    world.facts["plan"] = "shortcut failed"
    world.facts["risk"] = "the load could spill and the path could become slippery"
    world.para()

    world.say(
        f"{animal.label} stopped instead of rushing on. The important clue was that "
        f"{task['clue']}."
    )
    world.say(
        f'"Aha," said {animal.label}. "The ground is telling us where the carrier tips."'
    )
    world.say(
        f'"Then let us solve the problem, not fight it," said {helper.label}. '
        f'"We can use {task["fix"]}."'
    )
    world.say(
        f"They set the carrier down, checked the route with empty paws, and made "
        f"the safer plan together."
    )
    world.facts["plan"] = "pause, inspect, and choose a safer route"
    world.facts["final_route"] = task["fix"]
    animal.memes["caution"] = 1.0
    animal.memes["confidence"] = 0.85
    world.facts["spill_amount"] = "only a few drops"
    world.para()

    world.say(
        f"Step by careful step, {animal.label} carried the load along {task['fix']}."
    )
    world.say(
        f"The water still made a quiet slosh, but the carrier stayed level and "
        f"{task['cargo']} arrived safely."
    )
    world.say(
        f"At {task['destination']}, the animals cheered. The small spill became a "
        f"warning remembered, not a disaster repeated."
    )
    world.say(
        f"They ended the day with {task['image']}. {animal.label} had learned that "
        f"{task['lesson']}."
    )
    world.facts["resolved"] = True
    container.meters["stability"] = 0.95
    container.meters["fullness"] = 0.82
    animal.memes["caution"] = 1.0
    animal.memes["problem_solving"] = 1.0
    return world


def generation_prompts(world: World) -> list[str]:
    task = world.facts["task"]
    animal = world.facts["animal"].label
    return [
        f"Write an animal story about {animal} hearing a slosh while carrying {task['cargo']}.",
        f"Tell a cautionary problem-solving tale in which {animal} abandons a risky shortcut.",
        f"End with {task['image']} and show why checking the route matters.",
    ]


def story_qa(world: World) -> list[QAItem]:
    task = world.facts["task"]
    animal = world.facts["animal"].label
    return [
        QAItem(
            question=f"Why was {animal}'s first plan dangerous?",
            answer=(
                f"{animal} chose a shortcut near {task['problem']}. The carrier bumped, "
                f"the water began to slosh, and the whole load might have spilled."
            ),
        ),
        QAItem(
            question="What clue helped solve the problem?",
            answer=(
                f"The clue was that {task['clue']}. It showed where the carrier tipped "
                f"and helped the animals choose a safer route."
            ),
        ),
        QAItem(
            question="How did the animals change their plan?",
            answer=(
                f"They stopped, checked the route with an empty carrier, and used "
                f"{task['fix']} instead of forcing the shortcut."
            ),
        ),
        QAItem(
            question="What happened to the load?",
            answer=(
                f"The carrier stayed level, so the water and {task['cargo']} reached "
                f"{task['destination']} safely. Only a few drops were spilled."
            ),
        ),
        QAItem(
            question="What caution did the animal learn?",
            answer=(
                f"{animal} learned that {task['lesson']}. Pausing to inspect the path "
                f"made the delivery safe."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does slosh mean?",
            answer=(
                "Slosh means liquid moves noisily from side to side, especially when "
                "a container is carried or shaken."
            ),
        ),
        QAItem(
            question="Why can a heavy container be harder to carry?",
            answer=(
                "A heavy container can shift a carrier's balance. A careful carrier "
                "uses a level route, slows down, and rests when needed."
            ),
        ),
        QAItem(
            question="What is problem solving?",
            answer=(
                "Problem solving means noticing a difficulty, looking for useful clues, "
                "thinking of choices, and testing a safer solution."
            ),
        ),
        QAItem(
            question="Why is caution helpful?",
            answer=(
                "Caution helps an animal notice risks before they cause harm. It does "
                "not mean giving up; it means choosing actions thoughtfully."
            ),
        ),
    ]


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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type} {entity.label} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    for key in ("plan", "risk", "final_route", "spill_amount", "resolved"):
        lines.append(f"  fact.{key}={world.facts.get(key)}")
    return "\n".join(lines)


ASP_RULES = """
valid_story :-
    setting(animal_trail),
    feature(cautionary),
    feature(problem_solving),
    word(slosh),
    safe_route(chosen),
    resolved(true).
#show valid_story/0.
""".strip()


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("setting", "animal_trail"),
        asp.fact("feature", "cautionary"),
        asp.fact("feature", "problem_solving"),
        asp.fact("word", "slosh"),
        asp.fact("safe_route", "chosen"),
        asp.fact("resolved", "true"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program())
    accepted = any(symbol.name == "valid_story" for symbol in symbols)
    if not accepted:
        print("Mismatch: ASP rejected the cautionary problem-solving story.")
        return 1
    rng = random.Random(20260907)
    for _ in range(5):
        sample = generate(resolve_params(build_parser().parse_args([]), rng),)
        if "slosh" not in sample.story.lower() or not sample.world.facts["resolved"]:
            print("Mismatch: generated story failed its world checks.")
            return 1
    print("OK: ASP and Python accepted the safe slosh story.")
    return 0


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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="the ferny creek bank",
        animal_name="Mara",
        carrier="a blue tin pail",
        task_id="berries",
        opening_id=0,
        dialogue_id=0,
    ),
    StoryParams(
        place="the sunny orchard path",
        animal_name="Pip",
        carrier="a round wooden tub",
        task_id="seeds",
        opening_id=2,
        dialogue_id=1,
    ),
    StoryParams(
        place="the mossy pond trail",
        animal_name="Tavi",
        carrier="a bright green watering can",
        task_id="flowers",
        opening_id=4,
        dialogue_id=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        print("compatible story:")
        for symbol in asp.one_model(asp_program()):
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

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
