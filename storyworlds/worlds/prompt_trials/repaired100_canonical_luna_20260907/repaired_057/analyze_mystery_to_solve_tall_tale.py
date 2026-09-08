#!/usr/bin/env python3
"""
A child-friendly tall tale about analyzing a small mystery and solving it
through careful observation, testing, and teamwork.
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
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the enormous old town square"
    affords: set[str] = field(default_factory=lambda: {"observe", "measure", "solve"})


@dataclass
class Mystery:
    name: str
    problem: str
    first_guess: str
    clue: str
    test: str
    discovery: str
    solution: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    mystery: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


@dataclass
class StoryState:
    hero: Entity
    helper: Entity
    mystery: Mystery
    analyzed: bool = False
    solved: bool = False


SETTING = Setting()

MYSTERIES = {
    "bell": Mystery(
        name="the bell that rang by itself",
        problem="the giant brass bell atop the square's clock tower rang at noon, although nobody had pulled its rope",
        first_guess="Luna guessed that a sleepy giant must be hiding in the tower and tugging the bell",
        clue="a blue feather lay beside the rope, while the tower window stood open",
        test="they sprinkled flour on the tower steps and watched from behind the fountain",
        discovery="a gust pushed a blue kite through the open window, and its tail caught the bell rope",
        solution="they closed the window, freed the kite, and tied a bright warning ribbon above the tower door",
        ending="That evening the bell rang only when the clock keeper pulled it, and the rescued kite danced safely below",
        lesson="a very large guess can become a very small answer when you analyze the clues",
    ),
    "shadow": Mystery(
        name="the shadow with two hats",
        problem="a huge shadow crossed the square every morning, and people swore that a two-hatted giant marched past",
        first_guess="Luna guessed that a towering mayor was walking behind the bakery",
        clue="the shadow always bent when the bakery chimney puffed smoke",
        test="they placed paper flags around the square and watched which way each flag trembled",
        discovery="the shadow came from a tall weather vane and its long ribbon, stretched by the rising sun",
        solution="they untangled the ribbon and painted the weather vane's shape on a sign",
        ending="The next morning the shadow still stretched wide, but everyone greeted the harmless weather vane",
        lesson="analyze a mystery from more than one angle before calling it frightening",
    ),
    "drum": Mystery(
        name="the thunder under the bridge",
        problem="a deep boom shook the little bridge whenever the moon rose",
        first_guess="Luna guessed that a giant was drumming beneath the bridge",
        clue="the boom came only after rain, and bubbles rose beside the middle stone",
        test="they floated three leaf boats and marked where the current carried them",
        discovery="water rushed through a hollow log under the bridge and struck the stone like a drum",
        solution="they cleared the log's leafy doorway and set a small sign beside the safe crossing",
        ending="The next moon brought a gentle plunk instead of thunder, and the leaf boats sailed smoothly",
        lesson="careful tests can turn a scary sound into a useful explanation",
    ),
    "footprints": Mystery(
        name="the giant footprints in the garden",
        problem="round footprints appeared between the pumpkin vines, each one as wide as a wagon wheel",
        first_guess="Luna guessed that a giant had come to nibble the pumpkins",
        clue="the prints stopped at the old windmill, and tiny seeds filled their edges",
        test="they covered one patch with smooth sand and placed a lantern nearby",
        discovery="the windmill's loose wheel dragged a seed sack in circles after sunset",
        solution="they tightened the wheel and tied the sack to a sturdy post",
        ending="The next morning the garden held pumpkins, not footprints, and the windmill turned proudly",
        lesson="analyze where a mystery begins and ends before chasing a giant",
    ),
}

HERO_NAMES = ["Luna", "Milo", "Nell", "Toby", "Ivy", "Pip"]
HELPER_NAMES = ["Rae", "Finn", "Wren", "June", "Kit", "Sage"]

OPENINGS = (
    "In the enormous old town square, {hero} arrived with {helper}, whose pockets were full of string, chalk, and courage.",
    "One morning, when the town's rooster sneezed loud enough to rattle spoons, {hero} and {helper} found a mystery waiting in the square.",
    "The square was so wide that a pigeon needed a map to cross it. In the middle stood {hero} and {helper}, ready to investigate.",
    "At the old town square, {hero} wore a thinking cap and {helper} carried a notebook large enough to hold a tall tale.",
)

DIALOGUE = (
    "'Do not chase the biggest idea first,' said {helper}. 'Let us analyze what we can see.'",
    "{hero} tapped the notebook. 'A clue is stronger when we test it.'",
    "'I have a giant guess,' said {hero}, 'but I would rather have a careful answer.'",
    "{helper} smiled. 'Your eyes notice the clue, and mine can check the pattern.'",
)

ASP_RULES = r"""
mystery_present(m).
observes(hero, m).
has_clue(m).
analyzes(hero, m) :- observes(hero, m), has_clue(m).
tests(hero, m) :- analyzes(hero, m).
solved(m) :- tests(hero, m), has_explanation(m).
tall_tale_ending(m) :- solved(m).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tall-tale mystery-solving story world.")
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--mystery", choices=sorted(MYSTERIES))
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--helper-gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_type = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice([name for name in HELPER_NAMES if name != hero_name])
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    if mystery not in MYSTERIES:
        raise StoryError("That mystery is not in the town square's casebook.")
    if hero_name == helper_name:
        raise StoryError("The hero and helper need different names so their conversation is clear.")
    return StoryParams(hero_name, hero_type, helper_name, helper_type, mystery)


def tell_story(params: StoryParams) -> World:
    if params.mystery not in MYSTERIES:
        raise StoryError("The requested mystery has no clues to analyze.")

    mystery = MYSTERIES[params.mystery]
    world = World(SETTING)
    hero = world.add(Entity("hero", params.hero_type, params.hero_name))
    helper = world.add(Entity("helper", params.helper_type, params.helper_name))
    case = world.add(Entity("mystery", "mystery", mystery.name))

    variant = params.seed
    if variant is None:
        variant = sum((i + 1) * ord(c) for i, c in enumerate(params.hero_name + params.helper_name))
    world.say(OPENINGS[variant % len(OPENINGS)].format(hero=hero.label, helper=helper.label))
    world.say(f"Then {mystery.problem}. It was a mystery so grand that three goats fainted politely.")
    world.say(f"{mystery.first_guess}.")
    world.say(f"But {hero.label} noticed that {mystery.clue}.")
    world.say(DIALOGUE[(variant // 3) % len(DIALOGUE)].format(hero=hero.label, helper=helper.label))
    world.say(f"Together they {mystery.test}.")
    world.say(f"Their careful watching showed that {mystery.discovery}.")
    world.say(f"'Now we know what happened,' said {hero.label}. 'Let us fix the real problem.'")
    world.say(f"{mystery.solution}.")
    world.say(f"{mystery.ending}.")
    world.say(f"{hero.label} learned that {mystery.lesson}.")

    hero.meters.update({"attention": 1.0, "evidence": 1.0, "confidence": 1.0})
    helper.meters.update({"attention": 1.0, "evidence": 1.0, "confidence": 1.0})
    hero.memes.update({"curiosity": 1.0, "patience": 1.0, "teamwork": 1.0})
    helper.memes.update({"curiosity": 1.0, "patience": 1.0, "teamwork": 1.0})

    world.facts = {
        "hero": hero,
        "helper": helper,
        "case": case,
        "mystery": mystery,
        "analyzed": True,
        "solved": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        f"Write a tall tale in which {hero.label} analyzes {mystery.name} with help from {helper.label}.",
        f"Create a child-friendly mystery to solve using this clue: {mystery.clue}.",
        f"Tell a humorous town-square adventure where careful testing explains {mystery.problem}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            "Where did the mystery happen?",
            "It happened in the enormous old town square, including its tower, bridge, garden, or other nearby town places.",
        ),
        QAItem(
            f"What mystery did {hero.label} and {helper.label} investigate?",
            f"They investigated {mystery.name}: {mystery.problem}.",
        ),
        QAItem(
            f"What clue helped {hero.label} analyze the mystery?",
            f"The important clue was that {mystery.clue}.",
        ),
        QAItem(
            "How did the friends test their ideas?",
            f"They {mystery.test}. This gave them evidence instead of leaving them with only a guess.",
        ),
        QAItem(
            "How was the mystery solved?",
            f"They discovered that {mystery.discovery}, and then {mystery.solution}.",
        ),
        QAItem(
            "What did the tall tale teach?",
            f"It taught that {mystery.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does analyze mean?", "To analyze means to study something carefully by looking at its parts, clues, and patterns."),
        QAItem("What is a mystery?", "A mystery is something not yet understood that can be explained by finding clues and testing ideas."),
        QAItem("Why are tests useful?", "Tests are useful because they show whether an idea matches what really happens."),
        QAItem("What is a tall tale?", "A tall tale is a playful story with enormous, surprising, or exaggerated events."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"facts: analyzed={world.facts.get('analyzed')} solved={world.facts.get('solved')}")
    return "\n".join(lines)


def asp_facts() -> str:
    from storyworlds import asp
    return "\n".join(
        [
            asp.fact("mystery_present", "m"),
            asp.fact("observes", "hero", "m"),
            asp.fact("has_clue", "m"),
            asp.fact("has_explanation", "m"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    from storyworlds import asp
    model = asp.one_model(asp_program("#show analyzed/2.\n#show tests/2.\n#show solved/1."))
    return bool(asp.atoms(model, "analyzed")) and bool(asp.atoms(model, "tests")) and bool(asp.atoms(model, "solved"))


def asp_verify() -> int:
    if not asp_valid():
        print("Mismatch: the ASP mystery is not analyzable and solvable.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "analyze" not in sample.story.lower():
            print("Mismatch: generated story failed the analysis check.")
            return 1
    print("OK: ASP and Python agree that the mystery can be analyzed, tested, and solved.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "girl", "Rae", "girl", "bell", 1),
    StoryParams("Milo", "boy", "Wren", "girl", "shadow", 2),
    StoryParams("Nell", "girl", "Finn", "boy", "drum", 3),
    StoryParams("Toby", "boy", "June", "girl", "footprints", 4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(
            "#show mystery_present/1.\n"
            "#show observes/2.\n"
            "#show has_clue/1.\n"
            "#show analyzes/2.\n"
            "#show tests/2.\n"
            "#show solved/1.\n"
            "#show tall_tale_ending/1."
        ))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        from storyworlds import asp
        model = asp.one_model(asp_program("#show analyzes/2.\n#show tests/2.\n#show solved/1."))
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
            if index > max(100, args.n * 100):
                break

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero_name} investigates {MYSTERIES[sample.params.mystery].name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
