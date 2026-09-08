#!/usr/bin/env python3
"""
A small folk-tale world about Luna, a leap, a sore toe, and the kindness
that turns curiosity into a careful rescue.
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
    companion: str = "Grandmother"
    creature: str = "hare"
    place: str = "the sun-warmed hill"
    seed: Optional[int] = None


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"energy": 1.0, "comfort": 1.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"kindness": 0.0, "curiosity": 0.0, "courage": 0.0}
    )


@dataclass
class World:
    place: str
    child: Person
    companion: Person
    creature: str
    heat: float = 0.7
    toe_pain: float = 0.0
    curiosity: float = 0.0
    kindness: float = 0.0
    leap_made: bool = False
    creature_safe: bool = False
    clue: str = ""
    obstacle: str = ""
    first_plan: str = ""
    better_plan: str = ""
    lesson: str = ""
    ending_image: str = ""
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


NAMES = ["Luna", "Milo", "Nell", "Pip", "Tara", "Oren"]
COMPANIONS = ["Grandmother", "Uncle Rowan", "Aunt May", "Father"]
CREATURES = ["hare", "field mouse", "young fox", "hedgehog"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Folk-tale story world about Luna's leap and kindness."
    )
    parser.add_argument("--child")
    parser.add_argument("--companion")
    parser.add_argument("--creature")
    parser.add_argument("--place", default="the sun-warmed hill")
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


TALES = [
    {
        "opening": "Once, when the noon sun poured heat over the hill",
        "obstacle": "a thorny vine had caught the creature's hind paw beside a flat stone",
        "clue": "the creature stopped struggling whenever Luna stopped moving",
        "first_plan": "Luna wanted to leap straight over the stones and pull the vine free",
        "better_plan": "she shaded the creature with her scarf, cooled the stone with a little water, and asked her companion to snip the vine",
        "lesson": "kindness begins by making a frightened creature feel safe",
        "ending": "The freed creature gave one bright leap into the cool grass",
    },
    {
        "opening": "In the old days, when the heat shimmered above the hill",
        "obstacle": "a tiny creature had fallen into a dry hoofprint whose walls were too steep to climb",
        "clue": "small grains slid down the print whenever the creature kicked",
        "first_plan": "Luna thought she could leap across the hollow and scoop the creature up",
        "better_plan": "she laid her walking stick across the print and packed a gentle ramp of leaves beneath it",
        "lesson": "curiosity is wisest when it listens to what the ground is saying",
        "ending": "The little creature climbed the leaf ramp and vanished beneath a fern",
    },
    {
        "opening": "One golden afternoon, while the air held the day's heat",
        "obstacle": "a shiny ribbon had twisted around a low branch, and the creature kept reaching for it",
        "clue": "the ribbon led toward a nest hidden under the branch",
        "first_plan": "Luna wanted to leap up and snatch the shining thing",
        "better_plan": "she knelt, drew the creature away with a berry, and untied the ribbon without shaking the nest",
        "lesson": "a curious heart must notice who else may be depending on a quiet place",
        "ending": "The nest stayed still while the ribbon rested in Luna's pocket",
    },
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place != "the sun-warmed hill":
        raise StoryError("This folk tale only supports the sun-warmed hill.")
    return StoryParams(
        child=args.child or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        creature=args.creature or rng.choice(CREATURES),
        place=args.place,
    )


def generate_story(world: World, params: StoryParams) -> None:
    index = (params.seed or 0) % len(TALES)
    tale = TALES[index]
    world.obstacle = tale["obstacle"]
    world.clue = tale["clue"]
    world.first_plan = tale["first_plan"]
    world.better_plan = tale["better_plan"]
    world.lesson = tale["lesson"]
    world.ending_image = tale["ending"]

    world.say(
        f"{tale['opening']}, {world.child.name} walked with {world.companion.name} "
        f"across {world.place}."
    )
    world.say(
        f"Heat pressed against her cheeks, and a sharp pebble pricked her toe, "
        f"but curiosity tugged her onward."
    )
    world.toe_pain = 0.3
    world.curiosity = 1.0
    world.child.memes["curiosity"] = 1.0
    world.say(
        f"\"Did you hear that?\" asked {world.child.name}. "
        f"\"I heard a small cry beneath the wind.\""
    )
    world.say(
        f"\"Then we will look carefully,\" said {world.companion.name}. "
        f"\"A kind eye is better than a hurried hand.\""
    )
    world.say(
        f"Near a warm stone, {world.obstacle}. "
        f"{world.child.name} felt an eager thought rise inside: "
        f"\"I must fix this at once, before the poor creature grows afraid.\""
    )
    world.say(f"{world.first_plan}.")
    world.leap_made = True
    world.child.meters["energy"] -= 0.2
    world.child.memes["courage"] += 0.4
    world.say(
        f"She made the leap, but her sore toe landed on loose dust. "
        f"The dust slid away, and the creature shivered."
    )
    world.say(
        f"\"Stop,\" said {world.companion.name}. "
        f"\"What changed when you moved?\""
    )
    world.say(
        f"{world.child.name} held still. {world.clue.capitalize()}. "
        f"Her inner monologue became quiet enough to hear the answer: "
        f"\"The creature does not need speed. It needs space and gentleness.\""
    )
    world.say(
        f"Together they used a safer plan: {world.better_plan}."
    )
    world.kindness = 1.0
    world.child.memes["kindness"] = 1.0
    world.child.memes["curiosity"] += 0.5
    world.child.meters["comfort"] -= world.toe_pain
    world.creature_safe = True
    world.say(
        f"The {world.creature} became still, then trusted the quiet work. "
        f"At last, it was free."
    )
    world.say(
        f"\"Your leap brought us here,\" said {world.companion.name}, "
        f"\"but your kindness brought the creature home.\""
    )
    world.say(
        f"{world.child.name} rubbed her toe and smiled. "
        f"She understood that {world.lesson}."
    )
    world.say(f"{world.ending_image}.")
    world.child.memes["courage"] += 0.4
    world.child.meters["energy"] -= 0.1


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Where did {p.child} walk?",
            answer=f"{p.child} walked with {p.companion} across {p.place}.",
        ),
        QAItem(
            question=f"Why was {p.child}'s toe sore?",
            answer=f"A sharp pebble pricked {p.child}'s toe while heat pressed over the hill.",
        ),
        QAItem(
            question=f"What did {p.child} first try to do?",
            answer=f"{p.child} first tried to leap over the stones and help quickly.",
        ),
        QAItem(
            question=f"What clue changed {p.child}'s plan?",
            answer=world.clue.capitalize() + ".",
        ),
        QAItem(
            question=f"How did {p.child} help the {p.creature}?",
            answer=world.better_plan.capitalize() + ".",
        ),
        QAItem(
            question=f"What did {p.child} learn?",
            answer=f"{p.child} learned that {world.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can heat make a walk difficult?",
            answer="Heat can make a person tired and thirsty, so resting and drinking water can help.",
        ),
        QAItem(
            question="What is a leap?",
            answer="A leap is a jump that carries someone through the air.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means noticing another being's needs and helping without causing harm.",
        ),
        QAItem(
            question="Why is curiosity useful?",
            answer="Curiosity encourages careful questions and helps people notice important clues.",
        ),
    ]


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        f"Write a child-friendly folk tale about {params.child}, a leap, a sore toe, and heat.",
        f"Tell a story in which kindness and curiosity help {params.child} rescue a {params.creature}.",
        f"Use inner monologue to show how {params.child} changes from rushing to careful helping.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
place(sun_warmed_hill).
feature(leap).
feature(toe).
feature(heat).
virtue(kindness).
device(inner_monologue).
virtue(curiosity).
valid_story :- place(sun_warmed_hill), feature(leap), feature(toe),
               feature(heat), virtue(kindness), device(inner_monologue),
               virtue(curiosity).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "sun_warmed_hill"),
            asp.fact("feature", "leap"),
            asp.fact("feature", "toe"),
            asp.fact("feature", "heat"),
            asp.fact("virtue", "kindness"),
            asp.fact("device", "inner_monologue"),
            asp.fact("virtue", "curiosity"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/0."))
    if any(symbol.name == "valid_story" for symbol in model):
        print("OK: ASP and Python story gates agree.")
        return 0
    print("MISMATCH: ASP story gate failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(
        place=params.place,
        child=Person(params.child, "child"),
        companion=Person(params.companion, "companion"),
        creature=params.creature,
    )
    world.facts["params"] = params
    generate_story(world, params)
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
        print("--- world trace ---")
        print(asdict(sample.params))
        print(
            {
                "heat": sample.world.heat,
                "toe_pain": sample.world.toe_pain,
                "curiosity": sample.world.curiosity,
                "kindness": sample.world.kindness,
                "leap_made": sample.world.leap_made,
                "creature_safe": sample.world.creature_safe,
                "child_meters": sample.world.child.meters,
                "child_memes": sample.world.child.memes,
            }
        )
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        child="Luna",
        companion="Grandmother",
        creature="hare",
        place="the sun-warmed hill",
    ),
    StoryParams(
        child="Pip",
        companion="Uncle Rowan",
        creature="field mouse",
        place="the sun-warmed hill",
        seed=1,
    ),
    StoryParams(
        child="Nell",
        companion="Aunt May",
        creature="young fox",
        place="the sun-warmed hill",
        seed=2,
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
        except Exception as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        print("ASP model:", asp.one_model(asp_program("#show valid_story/0.")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
