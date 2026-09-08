#!/usr/bin/env python3
"""
A small superhero story world about thirteen clues, a helpful neighbor,
bravery, curiosity, and a foreshadowed rescue.
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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    neighbor_name: str
    setting: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    neighbor: Character
    setting: str
    clues_found: int = 0
    signal_checked: bool = False
    rescue_complete: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Luna", "Mira", "Pip", "Nora", "Tavi", "Sol", "June", "Kai"]
SETTINGS = [
    "the twelve-story apartment house",
    "the moonlit neighborhood plaza",
    "the old row of townhouses",
    "the bright rooftop garden",
    "the little street beside the library",
]

INCIDENTS = [
    {
        "title": "the thirteenth bell",
        "setup": "a silver bell rang thirteen times from the dark clock tower",
        "danger": "the tower's loose weather vane was about to fall onto the neighbor's garden gate",
        "clue": "a tiny flash appeared above the gate after each bell",
        "foreshadowing": "Earlier, Luna had noticed thirteen bright scratches on the tower's railing.",
        "first_action": "ran toward the gate without looking up",
        "hero_action": "raised her glowing shield and held it beneath the weather vane",
        "neighbor_action": "pulled the garden gate open so everyone could move away",
        "ending": "the repaired vane spun safely while the thirteenth bell became a cheerful signal",
    },
    {
        "title": "the thirteen blue sparks",
        "setup": "thirteen blue sparks skipped along the pavement outside the neighbor's home",
        "danger": "a broken power cable was hiding beneath a fallen sign",
        "clue": "each spark stopped beside the same painted star",
        "foreshadowing": "At breakfast, Luna had seen that very star flickering on a loose street sign.",
        "first_action": "reached for the sign to lift it",
        "hero_action": "used her wind power to push the sign away without touching the cable",
        "neighbor_action": "called the power workers and kept children behind the chalk line",
        "ending": "the streetlights returned, and thirteen blue stickers marked the safe repair",
    },
    {
        "title": "the rooftop rescue",
        "setup": "thirteen paper heroes fluttered from the neighbor's rooftop clothesline",
        "danger": "one paper hero was wrapped around a small weather sensor that had begun to spark",
        "clue": "the paper cape pointed toward the sensor whenever the wind changed",
        "foreshadowing": "Luna had heard the rooftop sensor chirp thirteen times before the trouble began.",
        "first_action": "climbed the outside stairs before asking what was wrong",
        "hero_action": "curiously studied the wind, then used a safe ribbon of light to free the sensor",
        "neighbor_action": "unplugged the roof battery after Luna gave the signal",
        "ending": "the thirteen paper heroes hung in a neat row beneath a quiet, blinking sensor",
    },
]

OPENINGS = [
    "The neighborhood was settling down when",
    "Just after sunset,",
    "On an ordinary evening that needed one extraordinary helper,",
    "While the streetlights painted gold circles on the ground,",
]

LESSONS = [
    "Luna learned that curiosity is strongest when it asks questions before taking risks.",
    "Bravery did not mean rushing ahead; it meant noticing danger and choosing a safe way to help.",
    "The neighbor's calm plan and Luna's curious eyes made a better team than either one alone.",
    "A small clue can foreshadow a big problem, but careful friends can still change the ending.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Thirteen-neighbor superhero story world.")
    parser.add_argument("--hero-name", choices=NAMES)
    parser.add_argument("--neighbor-name", choices=NAMES)
    parser.add_argument("--setting", choices=SETTINGS)
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
    hero = args.hero_name or rng.choice(NAMES)
    neighbor_choices = [name for name in NAMES if name != hero]
    neighbor = args.neighbor_name or rng.choice(neighbor_choices)
    setting = args.setting or rng.choice(SETTINGS)
    return StoryParams(hero_name=hero, neighbor_name=neighbor, setting=setting)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.neighbor_name:
        raise StoryError("The hero and neighbor need different names.")
    if params.setting not in SETTINGS:
        raise StoryError("That setting is not part of this neighborhood.")
    if not params.hero_name or not params.neighbor_name:
        raise StoryError("Both the hero and the neighbor need names.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    incident = rng.choice(INCIDENTS)
    opening = rng.choice(OPENINGS)
    lesson = rng.choice(LESSONS)

    hero = Character(
        name=params.hero_name,
        kind="young superhero",
        meters={"distance_to_danger": 18.0, "energy": 9.0},
        memes={"bravery": 1.0, "curiosity": 1.0},
    )
    neighbor = Character(
        name=params.neighbor_name,
        kind="neighbor",
        meters={"distance_to_safe_place": 6.0, "calm": 8.0},
        memes={"trust": 1.0, "care": 1.0},
    )
    world = World(hero=hero, neighbor=neighbor, setting=params.setting)

    world.clues_found = 13
    world.facts["incident"] = incident["title"]
    world.facts["foreshadowing"] = incident["foreshadowing"]
    world.facts["danger"] = incident["danger"]

    lines = [
        f"{hero.name} was a young superhero who watched over {params.setting}.",
        f"{opening} {incident['setup']}.",
        f"{incident['foreshadowing']}",
        f"{hero.name} counted all thirteen clues, but the danger was not a game: {incident['danger']}.",
        f"{hero.name} {incident['first_action']}.",
        f'"Wait," called {neighbor.name}, the neighbor. "Let us discover what the clues are telling us before we touch anything."',
        f'"You are right," said {hero.name}. "Curiosity can help me find the safe answer."',
        f"The useful clue was clear: {incident['clue']}.",
        f"{hero.name}'s Bravery did not make the danger disappear. Instead, it helped the hero pause, look, and choose a careful plan.",
        f"{hero.name} {incident['hero_action']}.",
        f"{neighbor.name} {incident['neighbor_action']}.",
        f'When the danger passed, {neighbor.name} smiled. "Your curiosity found the clue, and your bravery used it wisely."',
        f'"And your plan made the rescue safe," said {hero.name}.',
        lesson,
        f"At last, {incident['ending']}.",
    ]

    world.signal_checked = True
    world.rescue_complete = True
    world.facts["clue"] = incident["clue"]
    world.facts["hero_action"] = incident["hero_action"]
    world.facts["neighbor_action"] = incident["neighbor_action"]
    world.facts["lesson"] = lesson
    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Write a Superhero Story about {hero.name}, thirteen clues, and a helpful neighbor.",
        f"Show how Bravery and Curiosity help {hero.name} respond safely to {incident['title']}.",
        f"Include Foreshadowing before the rescue and let {neighbor.name}'s advice change the hero's plan.",
    ]

    story_qa = [
        QAItem(
            question=f"What did {hero.name} discover through Curiosity?",
            answer=f"{hero.name} discovered that {incident['clue']}.",
        ),
        QAItem(
            question="How did Foreshadowing prepare the reader for the danger?",
            answer=f"The story foreshadowed the danger by showing that {incident['foreshadowing'].lower()}",
        ),
        QAItem(
            question=f"How did {hero.name} show Bravery?",
            answer=f"{hero.name} showed Bravery by {incident['hero_action']}.",
        ),
        QAItem(
            question=f"How did {neighbor.name} help?",
            answer=f"{neighbor.name} helped by {incident['neighbor_action']}.",
        ),
        QAItem(
            question="Why did the hero pause before acting?",
            answer=f"The hero paused because {incident['danger']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means facing a difficult moment while making a careful, helpful choice.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn more by observing, asking questions, and checking clues.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an earlier hint that prepares readers for something that happens later.",
        ),
        QAItem(
            question="Why can a neighbor be an important helper?",
            answer="A neighbor can notice local details, share a calm plan, and help keep people safe.",
        ),
        QAItem(
            question="Why was thirteen important in this story?",
            answer="Thirteen gave the hero a careful set of clues to count and helped connect the early hint to the later rescue.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        world = sample.world
        print()
        print("--- trace ---")
        print(f"hero={world.hero.name}, kind={world.hero.kind}, meters={world.hero.meters}, memes={world.hero.memes}")
        print(
            f"neighbor={world.neighbor.name}, kind={world.neighbor.kind}, "
            f"meters={world.neighbor.meters}, memes={world.neighbor.memes}"
        )
        print(
            f"setting={world.setting}, clues_found={world.clues_found}, "
            f"signal_checked={world.signal_checked}, rescue_complete={world.rescue_complete}"
        )
    if qa:
        print()
        print("== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
valid_setting(S) :- setting(S).
safe_team(H,N) :- hero(H), neighbor(N), H != N.
thirteen_clues :- clue_count(13).
rescue_ready :- safe_team(H,N), thirteen_clues, foreshadowing, curiosity, bravery.
#show valid_setting/1.
#show rescue_ready/0.
"""


def asp_facts() -> str:
    import asp
    facts = [asp.fact("setting", setting) for setting in SETTINGS]
    facts.extend(
        [
            asp.fact("hero", "luna"),
            asp.fact("neighbor", "mira"),
            asp.fact("clue_count", 13),
            asp.fact("foreshadowing"),
            asp.fact("curiosity"),
            asp.fact("bravery"),
        ]
    )
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_settings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_setting/1."))
    return sorted(set(asp.atoms(model, "valid_setting")))


def asp_rescue_ready() -> bool:
    import asp
    model = asp.one_model(asp_program("#show rescue_ready/0."))
    return bool(asp.atoms(model, "rescue_ready"))


def asp_verify() -> int:
    python_settings = set((setting,) for setting in SETTINGS)
    clingo_settings = set(asp_valid_settings())
    if python_settings != clingo_settings:
        print("MISMATCH between clingo and Python settings.")
        print("  only in python:", sorted(python_settings - clingo_settings))
        print("  only in clingo:", sorted(clingo_settings - python_settings))
        return 1
    if not asp_rescue_ready():
        print("MISMATCH: clingo did not find the safe thirteen-clue rescue.")
        return 1

    for index, setting in enumerate(SETTINGS):
        params = StoryParams(
            hero_name=NAMES[index % len(NAMES)],
            neighbor_name=NAMES[(index + 1) % len(NAMES)],
            setting=setting,
            seed=index,
        )
        sample = generate(params)
        required = ["thirteen", "neighbor", "Bravery", "Curiosity"]
        if not all(word in sample.story for word in required):
            print("MISMATCH: generated story omitted a required narrative instrument.")
            return 1
        if not sample.world.rescue_complete:
            print("MISMATCH: generated story did not complete the rescue.")
            return 1

    print(f"OK: clingo matches {len(SETTINGS)} settings and generated stories pass.")
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(
                hero_name=NAMES[index % len(NAMES)],
                neighbor_name=NAMES[(index + 1) % len(NAMES)],
                setting=setting,
            )
            for index, setting in enumerate(SETTINGS)
        ]

    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + index)) for index in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_setting/1.\n#show rescue_ready/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(setting[0] for setting in asp_valid_settings()))
        print(f"rescue_ready={str(asp_rescue_ready()).lower()}")
        return

    samples: list[StorySample] = []
    for index, params in enumerate(generation_params(args)):
        params.seed = (args.seed if args.seed is not None else 0) + index
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
