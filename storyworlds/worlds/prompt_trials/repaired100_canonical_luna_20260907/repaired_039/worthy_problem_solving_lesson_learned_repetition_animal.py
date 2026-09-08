#!/usr/bin/env python3
"""A gentle animal storyworld about solving a worthy problem and learning by repetition."""

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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Animal:
    name: str
    species: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Pip"
    place: str = "the forest clearing"
    task: str = "carry warm apples to the old hedgehog"
    object_name: str = "the little cart"
    worthy: str = "a worthy act of care"


@dataclass(frozen=True)
class Scenario:
    key: str
    problem: str
    clue: str
    failed: str
    first_step: str
    second_step: str
    lesson: str
    ending: str


@dataclass
class World:
    params: StoryParams
    animals: dict[str, Animal] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SCENARIOS = [
    Scenario(
        "bridge",
        "A rain-swollen stream washed away the small branch bridge.",
        "Flat stones made a dry path when they were placed close together.",
        "Luna first pushed one large branch into the water, but it rolled away.",
        "Luna searched for flat stones.",
        "Pip tested each stone before Luna carried the next one.",
        "A good solver changes the plan when the first plan does not work.",
        "At sunset, tiny footprints crossed the new stone path in a neat row.",
    ),
    Scenario(
        "gate",
        "A thorny vine tangled the gate that led to the berry garden.",
        "The vine loosened whenever the animals pulled one strand at a time.",
        "Luna tugged at the whole knot, and the gate only groaned.",
        "Luna found the loose end of the vine.",
        "Pip held the gate while Luna pulled the same gentle motion again and again.",
        "Repetition can make a hard job easier when each try is careful.",
        "The gate swung open, and the animals shared berries with the waiting birds.",
    ),
    Scenario(
        "basket",
        "A basket of acorns tipped toward a muddy slope.",
        "The basket stayed steady when its heavy acorns were placed at the bottom.",
        "Luna tried to carry it quickly, and three acorns rolled away.",
        "Luna stopped and gathered the scattered acorns.",
        "Pip showed her how to walk slowly and repeat three small steps between rests.",
        "Careful practice is stronger than a hurried guess.",
        "The last acorn reached the oak tree, where a squirrel family had food for winter.",
    ),
    Scenario(
        "bell",
        "The warning bell beside the meadow path would not ring.",
        "Its clapper moved when the bell was tilted slightly to the left.",
        "Luna shook the bell harder, but the clapper stayed stuck.",
        "Luna watched the clapper instead of guessing.",
        "Pip tilted the bell, and Luna repeated the soft pull until it rang.",
        "Looking closely helps a team find a worthy solution.",
        "The clear bell call guided every small animal safely home.",
    ),
]


def make_world(params: StoryParams) -> World:
    if params.hero == params.helper:
        raise StoryError("hero and helper must be different animals")
    world = World(params=params)
    world.animals = {
        params.hero: Animal(params.hero, "fox", meters={"energy": 1.0}, memes={"hope": 0.7}),
        params.helper: Animal(params.helper, "mouse", meters={"energy": 1.0}, memes={"patience": 0.9}),
    }
    return world


def generate_story_world(params: StoryParams) -> World:
    world = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    scene = rng.choice(SCENARIOS)
    p = params

    world.say(f"{p.hero} the fox lived near {p.place} with {p.helper} the mouse.")
    world.say(f"One morning, they planned to {p.task}.")
    world.say(f"They knew the small journey was {p.worthy}, because someone needed their help.")
    world.para()

    world.say(scene.problem)
    world.say(f'"{scene.failed}" {p.hero} said after the first attempt.')
    world.say(f'{p.helper} pointed to a clue. "{scene.clue}"')
    world.say(f'"Then we can solve one small part at a time," said {p.helper}.')
    world.para()

    world.say(f"{p.hero} {scene.first_step}")
    world.say(f"{p.helper} {scene.second_step}")
    world.say("They repeated the useful motion slowly, checking their work after every try.")
    world.say(f'"Again, but gently," {p.hero} said. "{p.helper} replied, "Again, and together."')
    world.para()

    world.say(f"The plan worked. {scene.lesson}")
    world.say(scene.ending)
    world.say(f"{p.hero} smiled because the lesson was not only about {p.object_name}; it was about caring enough to keep learning.")

    world.animals[p.hero].memes.update(hope=1.0, confidence=0.9, patience=0.8)
    world.animals[p.helper].memes.update(patience=1.0, trust=1.0)
    world.facts.update(
        scenario=scene.key,
        problem=scene.problem,
        clue=scene.clue,
        failed_attempt=scene.failed,
        hero_action=scene.first_step,
        helper_action=scene.second_step,
        lesson=scene.lesson,
        ending=scene.ending,
        repetition=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write an animal story about {p.hero} and {p.helper} solving a worthy problem.",
        "Show how repetition and careful teamwork change a failed attempt into a success.",
        "End with a concrete image that proves the animals learned a lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p, f = world.params, world.facts
    return [
        QAItem(
            f"What worthy task were {p.hero} and {p.helper} trying to complete?",
            f"They were trying to {p.task}. They considered it worthy because another animal needed their care.",
        ),
        QAItem(
            "What problem stopped them at first?",
            f"{f['problem']} Their first attempt failed because {str(f['failed_attempt'])[0].lower() + str(f['failed_attempt'])[1:]}",
        ),
        QAItem(
            "What clue helped the animals choose a better plan?",
            f"They noticed that {str(f['clue'])[0].lower() + str(f['clue'])[1:]} This observation helped them solve the cause instead of guessing.",
        ),
        QAItem(
            "How did repetition help?",
            f"They repeated a careful motion, checked their work, and adjusted when needed. Repetition turned a difficult job into a series of manageable tries.",
        ),
        QAItem(
            "What lesson did the animals learn?",
            f"They learned that {f['lesson']} Their ending success showed that patience and teamwork can protect someone who needs help.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is problem solving?",
            "Problem solving means noticing a difficulty, studying useful clues, trying a plan, and changing the plan when it does not work.",
        ),
        QAItem(
            "Why can repetition be useful?",
            "Repetition gives someone chances to practice a careful action, notice mistakes, and improve instead of giving up after one attempt.",
        ),
        QAItem(
            "What makes an action worthy?",
            "An action is worthy when it has meaningful value, such as helping another creature, protecting something important, or learning how to do a job well.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {x}" for i, x in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).
worthy_task(H,K) :- hero(H), helper(K), worthy.
problem_solved(H,K) :- worthy_task(H,K), clue_found, repeated_careful_try.
lesson_learned(H,K) :- problem_solved(H,K).
"""

DEFAULT_PARAMS = StoryParams()


def asp_facts() -> str:
    import asp
    p = DEFAULT_PARAMS
    return "\n".join(
        [
            asp.fact("hero_name", p.hero),
            asp.fact("helper_name", p.helper),
            asp.fact("worthy"),
            asp.fact("clue_found"),
            asp.fact("repeated_careful_try"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    symbols = asp.one_model(asp_program("#show lesson_learned/2."))
    atoms = asp.atoms(symbols, "lesson_learned")
    if not atoms:
        print("MISMATCH: ASP lesson was not derived.")
        return 1
    sample = generate(StoryParams(seed=7))
    if not sample.story or not sample.story_qa:
        print("MISMATCH: generated story is incomplete.")
        return 1
    print("OK: ASP and Python agree on worthy problem solving.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--place")
    parser.add_argument("--task")
    parser.add_argument("--object-name", dest="object_name")
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
    heroes = ["Luna", "Milo", "Fern", "Clover"]
    helpers = ["Pip", "Toby", "Nell", "Bram"]
    places = ["the forest clearing", "the mossy hill", "the creek bank", "the meadow path"]
    tasks = [
        "carry warm apples to the old hedgehog",
        "bring dry leaves to a shivering nest",
        "return a lost duckling to its pond",
        "deliver berries to the hungry field mice",
    ]
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(heroes),
        helper=args.helper or rng.choice(helpers),
        place=args.place or rng.choice(places),
        task=args.task or rng.choice(tasks),
        object_name=args.object_name or "the little cart",
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
        f = sample.world.facts
        print(
            "\n--- trace ---\n"
            f"scenario={f['scenario']}\n"
            f"repetition={f['repetition']}\n"
            f"resolved={f['resolved']}"
        )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show lesson_learned/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program("#show lesson_learned/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(SCENARIOS) if args.all else max(1, args.n)
    samples: list[StorySample] = []

    for i in range(count):
        seed = base_seed + i
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
