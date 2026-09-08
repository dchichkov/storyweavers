#!/usr/bin/env python3
"""
A small folk-tale story world about chocolate, honest portrayals, transformation,
and a remembered lesson from the past.
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
    child: str = "Luna"
    elder: str = "Grandmother"
    village: str = "Cocoa Hollow"
    chocolate: str = "a moon-shaped chocolate cake"
    transformation: str = "honest"
    moral_value: str = "truthfulness"
    seed: Optional[int] = None


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"energy": 1.0, "courage": 0.2}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"honesty": 0.0, "kindness": 0.0, "wisdom": 0.0}
    )


@dataclass
class World:
    params: StoryParams
    child: Person
    elder: Person
    village: str
    chocolate: str
    memory: str = ""
    old_lesson: str = ""
    problem: str = ""
    clue: str = ""
    first_choice: str = ""
    better_choice: str = ""
    consequence: str = ""
    transformation: str = ""
    ending_image: str = ""
    chocolate_shared: bool = False
    truth_told: bool = False
    transformed: bool = False
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


NAME_POOL = ["Luna", "Mara", "Tavi", "Nia", "Rafi", "Elio"]
ELDER_POOL = ["Grandmother", "Grandfather", "Aunt Rosa", "Uncle Ben"]
VILLAGE_POOL = ["Cocoa Hollow", "Pepperwood", "Honey Hill"]
CHOCOLATE_POOL = [
    "a moon-shaped chocolate cake",
    "a basket of chocolate truffles",
    "a chocolate crown",
    "a warm chocolate loaf",
]
TRANSFORMATION_POOL = ["honest", "brave", "generous", "wise", "humble"]


TALES = [
    {
        "memory": "Long ago, Grandmother had once dropped a royal chocolate coin into a well and told the truth before anyone asked.",
        "old_lesson": "A truth may sting for a moment, but a lie can sour every sweet thing afterward.",
        "problem": "The village baker had placed a tiny silver bean inside the cake, but it disappeared before the festival.",
        "clue": "A dark chocolate smear crossed the edge of Luna's blue sleeve.",
        "first_choice": "thought about blaming the noisy crow that had flown over the cooling table",
        "better_choice": "showed the sleeve to the baker and told exactly what had happened",
        "consequence": "The baker found the silver bean beneath Luna's scarf, where it had fallen when she leaned over the cake.",
        "ending": "When the moon rose, the cake shone on the festival table, and every slice tasted sweeter because no one had been blamed unfairly.",
    },
    {
        "memory": "When Grandmother was young, she had broken the village bell and confessed before fear could turn the mistake into a rumor.",
        "old_lesson": "A mistake becomes smaller when it is carried into the light by honest hands.",
        "problem": "Luna was asked to portray the village harvest queen on a chocolate plaque, but her picture accidentally showed the queen's crooked crown.",
        "clue": "The crooked line matched a crack in the wooden ruler Luna had used.",
        "first_choice": "wanted to paint over the crooked crown and pretend the first drawing had never existed",
        "better_choice": "told the queen that the ruler had slipped and offered to redraw the plaque",
        "consequence": "The queen laughed kindly, wore the crooked crown for the festival, and asked Luna to keep the true little mark in the new portrait.",
        "ending": "The chocolate plaque rested by the hearth, portraying not perfection but a queen smiling at an honest mistake.",
    },
    {
        "memory": "Once, Grandfather had hidden a chocolate seed for winter and forgotten where he put it until he admitted he needed help.",
        "old_lesson": "Sharing a worry gives others a chance to turn it into a path.",
        "problem": "Luna promised to guard the village's largest chocolate basket, then noticed that one corner had melted in the sun.",
        "clue": "The basket's shadow had moved far from the cool stone cellar.",
        "first_choice": "considered covering the melted corner with fresh chocolate",
        "better_choice": "called the elder and explained that she had watched the basket too late",
        "consequence": "Together they moved the basket into the cellar and made small chocolate cups from the softened pieces.",
        "ending": "Children carried the new cups through the lanes, and Luna felt lighter because the truth had become a shared solution.",
    },
]


OPENINGS = [
    "In the old village of {village}, where chocolate was traded like treasure",
    "Beyond the green hills, in the folk-tale village of {village}",
    "At the edge of a forest, the people of {village} prepared their yearly chocolate feast",
    "In {village}, every child knew that sweet things carried important stories",
    "One golden morning in {village}, bells called everyone toward the village square",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Chocolate folk-tale story world.")
    parser.add_argument("--child")
    parser.add_argument("--elder")
    parser.add_argument("--village")
    parser.add_argument("--chocolate")
    parser.add_argument("--transformation", choices=TRANSFORMATION_POOL)
    parser.add_argument("--moral-value", default="truthfulness")
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
    moral = args.moral_value.strip()
    if not moral:
        raise StoryError("The moral value cannot be empty.")
    return StoryParams(
        child=args.child or rng.choice(NAME_POOL),
        elder=args.elder or rng.choice(ELDER_POOL),
        village=args.village or rng.choice(VILLAGE_POOL),
        chocolate=args.chocolate or rng.choice(CHOCOLATE_POOL),
        transformation=args.transformation or rng.choice(TRANSFORMATION_POOL),
        moral_value=moral,
    )


def make_world(params: StoryParams) -> World:
    return World(
        params=params,
        child=Person(params.child, "child"),
        elder=Person(params.elder, "elder"),
        village=params.village,
        chocolate=params.chocolate,
    )


def generate_story(world: World) -> None:
    params = world.params
    if params.seed is None:
        material = "|".join(asdict(params).get(k, "") or "" for k in asdict(params))
        number = int.from_bytes(
            hashlib.blake2b(material.encode(), digest_size=8).digest(), "big"
        )
    else:
        number = params.seed
    tale = TALES[number % len(TALES)]
    opening = OPENINGS[(number // len(TALES)) % len(OPENINGS)].format(
        village=world.village
    )

    world.memory = tale["memory"]
    world.old_lesson = tale["old_lesson"]
    world.problem = tale["problem"]
    world.clue = tale["clue"]
    world.first_choice = tale["first_choice"]
    world.better_choice = tale["better_choice"]
    world.consequence = tale["consequence"]
    world.ending_image = tale["ending"]
    world.transformation = params.transformation

    world.say(
        f"{opening}. {world.child.name} had been chosen to portray the village's "
        f"great chocolate tradition before the evening feast."
    )
    world.say(
        f"That morning, {world.child.name} carried {world.chocolate} toward the square "
        f"while {world.elder.name} followed with a lantern and a careful smile."
    )
    world.say(
        f"\"Remember that a portrayal should show what is true, not merely what looks grand,\" "
        f"said {world.elder.name}."
    )
    world.say(
        f"\"But what if the truth makes the story less beautiful?\" asked {world.child.name}."
    )
    world.say(
        f"\"Then let the truth teach the story how to become beautiful,\" replied {world.elder.name}."
    )
    world.say(world.problem)
    world.say(
        f"At first, {world.child.name} {world.first_choice}. "
        f"Then a quiet memory returned: {world.memory}"
    )
    world.say(
        f"{world.elder.name} noticed the hesitation. \"What did you see?\" "
        f"{world.elder.name} asked. \"Tell me before fear chooses your words.\""
    )
    world.say(f"\"I saw this,\" said {world.child.name}, pointing to {world.clue}")
    world.say(
        f"Instead of hiding the trouble, {world.child.name} {world.better_choice}. "
        f"{world.consequence}"
    )
    world.truth_told = True
    world.chocolate_shared = True
    world.child.memes["honesty"] += 1.0
    world.child.memes["wisdom"] += 0.5
    world.child.meters["courage"] += 0.8
    world.say(
        f"The elder nodded. \"That is {params.moral_value}: choosing the clear path "
        f"when a crooked one seems easier.\""
    )
    world.say(
        f"The people gathered around the chocolate, and {world.child.name} portrayed "
        f"the day's true lesson instead of polishing away its difficult part."
    )
    world.say(
        f"Because the truth had been spoken, the villagers solved the problem together "
        f"and shared the chocolate fairly."
    )
    world.transformed = True
    world.child.memes["kindness"] += 0.5
    world.child.memes["wisdom"] += 0.5
    world.say(
        f"By sunset, {world.child.name} had changed and felt truly {params.transformation}. "
        f"{world.ending_image}"
    )


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            f"What did {p.child} carry to the village square?",
            f"{p.child} carried {p.chocolate} to the village square.",
        ),
        QAItem(
            f"What problem did {p.child} face?",
            world.problem,
        ),
        QAItem(
            f"What did {p.child} remember in the middle of the problem?",
            world.memory,
        ),
        QAItem(
            f"Why did {p.child} reveal the truth?",
            f"{p.child} revealed the truth because the memory and the clue showed that honesty could solve the problem without unfairly blaming anyone.",
        ),
        QAItem(
            "What moral value did the elder explain?",
            f"The elder explained that {p.moral_value} means choosing a truthful path even when hiding a mistake seems easier.",
        ),
        QAItem(
            f"How did {p.child} change?",
            f"{p.child} became more {p.transformation} by telling the truth, accepting responsibility, and helping the village solve the problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is chocolate?",
            "Chocolate is a food made from cacao beans and often mixed with sugar or milk.",
        ),
        QAItem(
            "What does it mean to portray something?",
            "To portray something means to show or describe it so others can understand what it is like.",
        ),
        QAItem(
            "Why is truthfulness a useful moral value?",
            "Truthfulness is useful because honest words help people trust one another and solve problems fairly.",
        ),
    ]


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        f"Write a folk tale about {params.child} using chocolate to portray a moral value.",
        f"Tell a story in which a flashback helps {params.child} become {params.transformation}.",
        f"Write a child-friendly tale about transformation through {params.moral_value}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
place(village).
material(chocolate).
theme(transformation).
moral_value(V) :- chosen_value(V).
flashback_used.
valid_story :- place(village), material(chocolate), theme(transformation),
               moral_value(_), flashback_used.
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "village"),
            asp.fact("material", "chocolate"),
            asp.fact("chosen_value", "truthfulness"),
            asp.fact("flashback_used"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    if any(symbol.name == "valid_story" for symbol in model):
        sample = generate(
            StoryParams(seed=17, child="Luna", elder="Grandmother")
        )
        if sample.world and sample.world.truth_told and sample.world.transformed:
            print("OK: ASP and Python story gates agree.")
            return 0
    print("MISMATCH: ASP/Python parity check failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    world.facts["params"] = params
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(params),
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
        world = sample.world
        print("--- world trace ---")
        print(asdict(sample.params))
        print(
            {
                "child_meters": world.child.meters,
                "child_memes": world.child.memes,
                "truth_told": world.truth_told,
                "chocolate_shared": world.chocolate_shared,
                "transformed": world.transformed,
            }
        )
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        child="Luna",
        elder="Grandmother",
        village="Cocoa Hollow",
        chocolate="a moon-shaped chocolate cake",
        transformation="honest",
        moral_value="truthfulness",
        seed=0,
    ),
    StoryParams(
        child="Mara",
        elder="Grandfather",
        village="Pepperwood",
        chocolate="a chocolate crown",
        transformation="brave",
        moral_value="responsibility",
        seed=1,
    ),
    StoryParams(
        child="Tavi",
        elder="Aunt Rosa",
        village="Honey Hill",
        chocolate="a basket of chocolate truffles",
        transformation="generous",
        moral_value="kindness",
        seed=2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())

    if args.show_asp:
        print(asp_program())
        return

    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        print("ASP model:", asp.one_model(asp_program()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2))
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
