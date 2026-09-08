#!/usr/bin/env python3
"""
A small mystery storyworld about a jog, a flashback, and a missing blue ribbon.

Luna remembers a clue from an earlier jog and uses it to solve a gentle park mystery.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
)
sys.path.insert(0, REPO_ROOT)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass(frozen=True)
class MysteryCase:
    case_id: str
    object_name: str
    setup: str
    flashback: str
    clue: str
    trouble: str
    guess: str
    test: str
    twist: str
    repair: str
    ending: str


@dataclass
class StoryParams:
    hero_name: str
    helper_name: str
    case_id: str = "ribbon_bench"
    telling_mode: str = "clue_first"
    detail_id: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


CASES = {
    "ribbon_bench": MysteryCase(
        case_id="ribbon_bench",
        object_name="a blue running ribbon",
        setup="At the park gate, the little race ribbon was gone from the notice board",
        flashback="Luna remembered seeing a blue thread flutter beside the old bench during her morning jog",
        clue="a small blue thread still clung to a splinter on the bench",
        trouble="the children could not tell whether the ribbon had been taken or blown away",
        guess="that a gust had carried it into the bushes",
        test="follow the blue thread from the bench and compare it with the ribbon's torn edge",
        twist="the ribbon had caught on the bench, then a squirrel had tugged it toward its nest",
        repair="lift the ribbon gently from the nest and pin it back with a smooth card",
        ending="the blue ribbon waved safely on the notice board while the squirrel watched from a nearby branch",
    ),
    "missing_whistle": MysteryCase(
        case_id="missing_whistle",
        object_name="a silver whistle",
        setup="The coach's silver whistle vanished before the friendly jog began",
        flashback="During yesterday's jog, Luna remembered hearing a bright whistle near the fountain",
        clue="three damp footprints curved from the fountain toward the flower shed",
        trouble="everyone searched the track while the whistle was somewhere off the path",
        guess="that another runner had carried it home by mistake",
        test="walk the footprint trail and ask the gardener what had been moved near the shed",
        twist="the gardener had placed the whistle on a hook after finding it beside a puddle",
        repair="thank the gardener and hang the whistle on the coach's marked hook",
        ending="the coach gave one cheerful toot, and the jog began beneath the clear morning sky",
    ),
    "map_in_the_grass": MysteryCase(
        case_id="map_in_the_grass",
        object_name="a hand-drawn jogging map",
        setup="A hand-drawn map disappeared from Luna's backpack before the trail game",
        flashback="On her last jog, Luna remembered stopping where yellow flowers grew beside a split stone",
        clue="a yellow petal rested inside the backpack's loose side pocket",
        trouble="the team could not find the map's starting mark",
        guess="that the map had fallen somewhere along the longest path",
        test="return to the split stone and search only where the yellow petals had blown",
        twist="the map had slipped through the pocket and landed under the flower sign",
        repair="dry the map, redraw its starting mark, and fasten the pocket with a bright button",
        ending="the repaired map led everyone on a happy jog around the lake",
    ),
    "bell_on_the_path": MysteryCase(
        case_id="bell_on_the_path",
        object_name="a tiny silver bell",
        setup="A tiny silver bell from the park's kindness cart was missing",
        flashback="On an earlier jog, Luna had heard a soft jingle whenever she passed the willow tree",
        clue="a curved mark in the mud ended beside a low willow branch",
        trouble="the bell was needed to call children back from the far trail",
        guess="that the bell had rolled all the way to the pond",
        test="trace the mud mark, listen beneath the willow, and ask who had watered the tree",
        twist="the bell was caught in the watering cart's loose strap",
        repair="free the bell, tighten the strap, and place the bell back on the kindness cart",
        ending="the bell chimed from the cart as every jogger returned safely for lemonade",
    ),
}

MODES = ("clue_first", "flashback_first", "dialogue_first", "quiet_first")

OPENINGS = {
    "clue_first": "{hero} noticed one blue thread beside the park path.",
    "flashback_first": "Before the mystery began, {hero} remembered an earlier jog.",
    "dialogue_first": "'Something is missing,' said {helper}, as {hero} tied a shoe.",
    "quiet_first": "The park was quiet except for birds, shoes, and one faint sound.",
}

BRIDGES = (
    "Luna kept the detail in mind instead of rushing to a guess.",
    "They marked the spot with a pebble and promised not to disturb the clue.",
    "The clue seemed tiny, but tiny clues can open large questions.",
    "Luna slowed her breathing and looked at the ground again.",
)

REPLIES = (
    "'Let's check before we decide,' said {hero}.",
    "'A memory can help us notice what we missed,' said {helper}.",
    "'We need evidence, not just a good guess,' {hero} replied.",
    "'Look, listen, and follow the trail,' said {helper}.",
)


def story_reasonable(case_id: str) -> bool:
    return case_id in CASES


def explain_rejection(case_id: str) -> str:
    return f"(No story: the mystery case '{case_id}' is not in the jog registry.)"


def tell(params: StoryParams) -> World:
    if not story_reasonable(params.case_id):
        raise StoryError(explain_rejection(params.case_id))
    case = CASES[params.case_id]
    world = World()
    hero = world.add(Entity(params.hero_name, "character", params.hero_name))
    helper = world.add(Entity(params.helper_name, "character", params.helper_name))
    path = world.add(Entity("park_path", "place", "the park path"))
    clue = world.add(Entity("clue", "clue", case.clue))
    hero.add_meter("jog_distance", 1.0)
    hero.add_meme("curiosity", 2.0)
    helper.add_meme("trust", 1.0)
    world.facts.update(hero=hero, helper=helper, path=path, clue=clue, case=case)

    mode = params.telling_mode if params.telling_mode in OPENINGS else MODES[0]
    world.say(OPENINGS[mode].format(hero=hero.label, helper=helper.label))
    world.say(
        f"In the small park, {hero.label} and {helper.label} planned a gentle jog "
        f"past the fountain, the willow, and the old bench."
    )
    world.say(f"{case.setup}. It was {case.object_name}.")
    world.say(f"Then a flashback came to {hero.label}: {case.flashback}.")
    world.say(f"{case.clue}.")
    world.say(BRIDGES[params.detail_id % len(BRIDGES)])
    world.say(f"The mystery grew because {case.trouble}.")
    world.say(f"At first, they thought {case.guess}.")
    world.say(REPLIES[(params.detail_id + 1) % len(REPLIES)].format(hero=hero.label, helper=helper.label))
    world.say(
        f"Instead of chasing guesses, they decided to {case.test}. "
        "They moved carefully and left every other clue where they found it."
    )
    world.say(f"At last, the twist appeared: {case.twist}.")
    world.say(
        f"{hero.label} and {helper.label} worked together to {case.repair}. "
        f"'The flashback helped us notice the right place,' said {hero.label}. "
        f"'And the clue helped us know what to do,' answered {helper.label}."
    )
    world.say(f"After that, they remembered that {case.object_name} was easier to find when people looked calmly.")
    world.say(case.ending)
    return world


def generation_prompts(world: World) -> list[str]:
    case: MysteryCase = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly mystery about {hero.label} solving a park problem during a jog.",
        f"Use a flashback in which {hero.label} remembers this clue: {case.clue}.",
        f"Include a wrong guess, a fair test, the twist that {case.twist}, and a concrete ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: MysteryCase = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What was missing during {hero.label}'s jog?",
            f"They were looking for {case.object_name}. It mattered because {case.trouble}.",
        ),
        QAItem(
            "What did the flashback help Luna remember?",
            f"The flashback reminded Luna that {case.flashback}.",
        ),
        QAItem(
            "What clue moved the mystery forward?",
            f"The clue was that {case.clue}. It pointed the runners toward the truth.",
        ),
        QAItem(
            "What did the characters first guess?",
            f"They first guessed {case.guess}, but they checked that idea instead of trusting it.",
        ),
        QAItem(
            "How did they solve the mystery?",
            f"They decided to {case.test}. The test showed that {case.twist}.",
        ),
        QAItem(
            f"What did {hero.label} and {helper.label} do at the end?",
            f"Together they chose to {case.repair}. Then {case.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a jog?",
            "A jog is a gentle run, usually slower than a race.",
        ),
        QAItem(
            "What is a flashback?",
            "A flashback is a moment in a story that shows something remembered from earlier.",
        ),
        QAItem(
            "Why are clues useful in a mystery?",
            "Clues are useful because they give evidence that helps people test ideas and discover what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_case/1.
valid_case(C) :- mystery_case(C), has_jog(C), has_flashback(C), has_clue(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for case_id in CASES:
        lines.extend(
            [
                asp.fact("mystery_case", case_id),
                asp.fact("has_jog", case_id),
                asp.fact("has_flashback", case_id),
                asp.fact("has_clue", case_id),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_case/1."))
    return sorted(set(asp.atoms(model, "valid_case")))


def asp_verify() -> int:
    asp_set = {row[0] for row in asp_valid_cases()}
    py_set = set(CASES)
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python registry ({len(py_set)} cases).")
        for index, case_id in enumerate(sorted(py_set)):
            sample = generate(
                StoryParams(
                    hero_name="Luna",
                    helper_name="Milo",
                    case_id=case_id,
                    telling_mode=MODES[index % len(MODES)],
                    detail_id=index,
                    seed=index,
                )
            )
            if not sample.story or "Luna" not in sample.story or "flashback" not in sample.story.lower():
                print(f"Generated story check failed for {case_id}.")
                return 1
        print("OK: generated stories include the hero and flashback.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Jog flashback mystery storyworld.")
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--case-id", choices=sorted(CASES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: Optional[int] = None,
) -> StoryParams:
    hero_name = getattr(args, "hero_name", None) or rng.choice(["Luna", "Maya", "Noah", "Pip", "Iris"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(["Milo", "Ari", "Nia", "Sam", "June"])
    index = sample_seed if sample_seed is not None else rng.randrange(2**31)
    case_id = getattr(args, "case_id", None) or tuple(CASES)[index % len(CASES)]
    mode = MODES[(index // len(CASES)) % len(MODES)]
    detail_id = (index // (len(CASES) * len(MODES))) % len(BRIDGES)
    return StoryParams(
        hero_name=hero_name,
        helper_name=helper_name,
        case_id=case_id,
        telling_mode=mode,
        detail_id=detail_id,
        seed=sample_seed,
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity_id, entity in world.entities.items():
        lines.append(
            f"{entity_id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
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


CURATED = [
    StoryParams("Luna", "Milo", "ribbon_bench", "clue_first", 0),
    StoryParams("Maya", "Ari", "missing_whistle", "flashback_first", 1),
    StoryParams("Noah", "Nia", "map_in_the_grass", "dialogue_first", 2),
    StoryParams("Iris", "June", "bell_on_the_path", "quiet_first", 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_case/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(row[0] for row in asp_valid_cases()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            sample_seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
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
        header = f"### variant {index + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
