#!/usr/bin/env python3
"""
A tall tale about a ragamuffin, a mountain of lasagne, and the intelligence
needed to solve an unusually saucy problem.
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
import hashlib
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    place: str = "the town square"
    child: str = "Luna"
    companion: str = "Aunt Bea"
    quest: str = "carry the giant lasagne to the harvest table"
    transformation: str = "clever"
    commitment: str = "use intelligence before using strength"
    seed: Optional[int] = None


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"energy": 1.0, "hunger": 0.2, "balance": 0.5}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"intelligence": 0.4, "confidence": 0.2, "patience": 0.3}
    )


@dataclass
class World:
    place: str
    child: Person
    companion: Person
    object_name: str = "the giant lasagne"
    problem: str = ""
    clue: str = ""
    first_attempt: str = ""
    method: str = ""
    result: str = ""
    lesson: str = ""
    ending: str = ""
    committed: bool = False
    problem_solved: bool = False
    feast_ready: bool = False
    transformed: bool = False
    items: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


PROBLEMS = [
    {
        "title": "the lasagne avalanche",
        "problem": "The lasagne was taller than the clock tower, and its top noodles began sliding toward the mayor's hat.",
        "clue": "Luna noticed that every layer stayed firm where the cheese had cooled beside the square's shady fountain.",
        "first_attempt": "Luna tried to push the lasagne straight ahead, but one enormous noodle wrapped around a lamppost.",
        "method": "She used the fountain's cool shade as a safe resting place, slid broad serving boards underneath, and moved the dish one layer at a time.",
        "result": "The layers crossed the square in a steady procession, and not one tomato dropped on the mayor.",
        "lesson": "a huge problem can become manageable when intelligence divides it into small, careful steps",
        "ending": "At sunset, the lasagne stood on the harvest table like a golden red mountain with one parsley flag at its peak.",
        "items": ["serving boards", "parsley flag"],
    },
    {
        "title": "the sauce river",
        "problem": "A crack in the bottom dish released a red sauce river that flowed around the flower sellers' boots.",
        "clue": "The sauce slowed whenever it reached the square's shallow cobblestone gutters.",
        "first_attempt": "Luna grabbed a bucket and chased the river, but the sauce simply split into three smaller rivers.",
        "method": "She mapped the gutters with chalk, placed clean pans at their ends, and asked the bakers to lift the lasagne onto a sturdy tray.",
        "result": "The sauce was gathered instead of wasted, and the lasagne reached the table with its layers still delicious.",
        "lesson": "problem solving means studying where a difficulty wants to go before trying to stop it",
        "ending": "Three sauce pans gleamed beside the feast while a red chalk map curled across the square.",
        "items": ["chalk map", "sturdy tray"],
    },
    {
        "title": "the noodle knot",
        "problem": "A hundred miles of lasagne noodle had tangled around the wagon wheels, tying the feast to the fountain.",
        "clue": "The knot loosened whenever the wagon rolled backward a little before turning.",
        "first_attempt": "Luna pulled the longest noodle with all her might, and the knot answered by tying her scarf to a cabbage.",
        "method": "She marked the loose end, rolled the wagon backward, and unwound the noodles in the same order they had wrapped.",
        "result": "The wagon came free, the scarf was rescued, and the lasagne remained gloriously intact.",
        "lesson": "intelligence often begins by finding the order in which a problem was made",
        "ending": "The last noodle curled onto the table in a perfect spiral beside Luna's rescued scarf.",
        "items": ["chalk marker", "rescued scarf"],
    },
    {
        "title": "the cheese moon",
        "problem": "A round lid of melted cheese had floated into the sky and blocked the sun over the harvest table.",
        "clue": "The cheese drifted lower whenever the town band played a soft, low note.",
        "first_attempt": "Luna waved a broom at the cheese moon, but it only spun faster and sprinkled parmesan on the pigeons.",
        "method": "She asked the band to play the low note, guided the cheese toward a waiting giant platter, and let its own weight bring it down.",
        "result": "The sky brightened, the pigeons were dusted clean, and the lasagne gained a shining golden lid.",
        "lesson": "a calm experiment can reveal a better tool than force",
        "ending": "The cheese moon rested on the lasagne while sunlight returned to every spoon in the square.",
        "items": ["giant platter", "brass band"],
    },
]


OPENINGS = [
    "On the largest lunch day the town had ever measured",
    "In a square so small that one enormous sneeze could move every hat",
    "At the annual Feast of Extra Helpings",
    "On a bright morning when the bells rang louder than usual",
    "During the grandest harvest celebration in local memory",
]

PROMISES = [
    "said the promise aloud",
    "tied a red thread around one finger as a reminder",
    "asked the nearest grown-up to hold her to the plan",
    "wrote the promise on a flour sack",
    "stood on a crate and announced the promise to the pigeons",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ragamuffin lasagne intelligence problem-solving world.")
    parser.add_argument("--place", choices=["the town square"], default="the town square")
    parser.add_argument("--child")
    parser.add_argument("--companion")
    parser.add_argument("--quest")
    parser.add_argument("--transformation")
    parser.add_argument("--commitment")
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


NAME_POOL = ["Luna", "Pip", "Mara", "Tavi", "Nell"]
COMPANION_POOL = ["Aunt Bea", "Uncle Sol", "Grandma Jo", "Chef Odo"]
TRANSFORMATIONS = ["clever", "patient", "inventive", "thoughtful"]
QUESTS = [
    "carry the giant lasagne to the harvest table",
    "save the giant lasagne before the feast begins",
    "guide the giant lasagne across the town square",
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place != "the town square":
        raise StoryError("This tall tale only supports the town square.")
    commitment = args.commitment or "use intelligence before using strength"
    return StoryParams(
        place=args.place,
        child=args.child or rng.choice(NAME_POOL),
        companion=args.companion or rng.choice(COMPANION_POOL),
        quest=args.quest or rng.choice(QUESTS),
        transformation=args.transformation or rng.choice(TRANSFORMATIONS),
        commitment=commitment,
    )


def make_world(params: StoryParams) -> World:
    return World(
        place=params.place,
        child=Person(params.child, "ragamuffin"),
        companion=Person(params.companion, "helper"),
    )


def choose_problem(params: StoryParams) -> dict:
    material = f"{params.child}|{params.companion}|{params.quest}|{params.commitment}|{params.seed}"
    number = int.from_bytes(hashlib.blake2b(material.encode(), digest_size=8).digest(), "big")
    return PROBLEMS[number % len(PROBLEMS)]


def generate_story(world: World, params: StoryParams) -> None:
    problem = choose_problem(params)
    world.problem = problem["problem"]
    world.clue = problem["clue"]
    world.first_attempt = problem["first_attempt"]
    world.method = problem["method"]
    world.result = problem["result"]
    world.lesson = problem["lesson"]
    world.ending = problem["ending"]
    world.items.extend(problem["items"])

    seed = params.seed or 0
    mode = seed % len(OPENINGS)
    promise_beat = PROMISES[(seed // len(OPENINGS)) % len(PROMISES)]

    world.say(
        f"{OPENINGS[mode]}, {world.child.name}, a cheerful ragamuffin with two unmatched socks, "
        f"arrived at {world.place} beside {world.companion.name}."
    )
    world.say(
        f"A lasagne as wide as a barn door waited on a wagon. {world.child.name} {promise_beat}: "
        f"\"I will {params.commitment}.\""
    )
    world.committed = True
    world.child.memes["intelligence"] += 0.3
    world.child.meters["energy"] -= 0.1
    world.say(
        f"\"Good,\" said {world.companion.name}. \"A strong back is useful, but what will guide it?\" "
        f"\"A question, a clue, and a plan,\" replied {world.child.name}."
    )
    world.say(f"Then came {problem['title']}. {problem['problem']}")
    world.say(
        f"At first, {world.child.name} {problem['first_attempt']} "
        f"\"Stop!\" cried {world.companion.name}. \"What did you learn?\""
    )
    world.say(
        f"\"The trouble has a pattern,\" said {world.child.name}. {problem['clue']} "
        f"\"Then let us solve the cause, not merely wrestle the result,\" said {world.companion.name}."
    )
    world.say(problem["method"])
    world.say(problem["result"])
    world.problem_solved = True
    world.child.memes["intelligence"] += 0.8
    world.child.memes["confidence"] += 0.5
    world.child.meters["energy"] -= 0.25
    world.say(
        f"After that, {world.child.name} and {world.companion.name} completed the quest to "
        f"{params.quest}, using the same careful plan for every remaining step."
    )
    world.feast_ready = True
    world.say(
        f"The town cheered, but {world.child.name} only smiled. {world.lesson.capitalize()}."
    )
    world.transformed = True
    world.child.memes["patience"] += 0.6
    world.say(
        f"By the end, the ragamuffin felt {params.transformation}, and {problem['ending']}"
    )


def make_story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    return [
        QAItem(
            question=f"Who was the ragamuffin in the story?",
            answer=f"{params.child} was the ragamuffin who used intelligence to solve the lasagne problem.",
        ),
        QAItem(
            question=f"What did {params.child} promise to do?",
            answer=f"{params.child} promised to {params.commitment}.",
        ),
        QAItem(
            question=f"What went wrong with the lasagne?",
            answer=world.problem,
        ),
        QAItem(
            question=f"What clue helped {params.child}?",
            answer=world.clue,
        ),
        QAItem(
            question=f"Why did {params.child} stop the first attempt?",
            answer=(
                f"{params.child} stopped because the first attempt did not address the real pattern "
                f"of the problem. The clue suggested a safer, more intelligent method."
            ),
        ),
        QAItem(
            question="How was the problem solved?",
            answer=world.method,
        ),
        QAItem(
            question=f"How did the adventure change {params.child}?",
            answer=(
                f"{params.child} became {params.transformation} by learning that {world.lesson}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is lasagne?",
            answer="Lasagne is a layered dish usually made with pasta, sauce, cheese, and other fillings.",
        ),
        QAItem(
            question="What does intelligence help someone do?",
            answer="Intelligence can help someone notice patterns, ask useful questions, make plans, and solve problems.",
        ),
        QAItem(
            question="What is a ragamuffin?",
            answer="A ragamuffin is a person who looks untidy or wears patched, ragged clothes.",
        ),
    ]


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        f"Write a tall tale about {params.child}, a ragamuffin who must solve a giant lasagne problem.",
        f"Tell a child-friendly problem-solving story in {params.place} where intelligence matters more than strength.",
        f"Write a humorous tall tale about how {params.child} becomes {params.transformation}.",
    ]


def format_qa(sample: StorySample) -> str:
    sections = ["== Generation prompts =="]
    sections.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    sections.append("\n== Story Q&A ==")
    for item in sample.story_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    sections.append("\n== World Q&A ==")
    for item in sample.world_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(sections)


ASP_RULES = r"""
place(town_square).
dish(lasagne).
role(ragamuffin).
skill(intelligence).
method(problem_solving).
valid_story :-
    place(town_square),
    dish(lasagne),
    role(ragamuffin),
    skill(intelligence),
    method(problem_solving).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "town_square"),
            asp.fact("dish", "lasagne"),
            asp.fact("role", "ragamuffin"),
            asp.fact("skill", "intelligence"),
            asp.fact("method", "problem_solving"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if any(symbol.name == "valid_story" for symbol in model):
        rng = random.Random(17)
        sample = generate(resolve_params(build_parser().parse_args([]), rng))
        if sample.story and sample.story_qa and "lasagne" in sample.story.lower():
            print("OK: ASP/Python parity and generated story checks passed.")
            return 0
    print("MISMATCH: ASP/Python parity check failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    world.facts["params"] = params
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(params),
        story_qa=make_story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        print(asdict(sample.params))
        print(
            {
                "child_meters": sample.world.child.meters,
                "child_memes": sample.world.child.memes,
                "problem_solved": sample.world.problem_solved,
                "feast_ready": sample.world.feast_ready,
                "transformed": sample.world.transformed,
                "items": sample.world.items,
            }
        )
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        child="Luna",
        companion="Aunt Bea",
        quest="carry the giant lasagne to the harvest table",
        transformation="clever",
        commitment="use intelligence before using strength",
        seed=7,
    ),
    StoryParams(
        child="Pip",
        companion="Chef Odo",
        quest="save the giant lasagne before the feast begins",
        transformation="patient",
        commitment="look for a clue before making a big move",
        seed=19,
    ),
    StoryParams(
        child="Mara",
        companion="Grandma Jo",
        quest="guide the giant lasagne across the town square",
        transformation="inventive",
        commitment="solve one small part at a time",
        seed=31,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return

    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program("#show valid_story/0."))
        except Exception as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        print("ASP model:", model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
