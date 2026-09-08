#!/usr/bin/env python3
"""
A tall tale world about organizing a gift, evaluating a huge surprise, and
earning a happy ending.

Seed words: organize, gift, evaluate
Feature: Happy Ending
Style: Tall Tale
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = [
    "the hilltop village",
    "the windy harbor town",
    "the valley fairground",
    "the little mountain city",
]
HERO_NAMES = ["Luna", "Mara", "Pip", "Tessa", "Nell", "Jo"]
HELPER_NAMES = ["Bram", "Otto", "Mina", "Sol", "Ada", "Finn"]
HERO_KINDS = ["cartographer", "baker", "gardener", "bell maker", "boat builder"]
HELPER_KINDS = ["librarian", "farmer", "cobbler", "musician", "weather watcher"]
GIFT_TYPES = [
    "a moon-bright quilt",
    "a clockwork kite",
    "a mountain of cinnamon buns",
    "a silver garden gate",
    "a singing wooden wagon",
]
MATERIALS = ["blue cloth", "maple wood", "warm wool", "polished tin", "red ribbon"]

TALES = [
    {
        "title": "the cloud-high parcel",
        "goal": "organize a surprise gift for the village children",
        "problem": "the gift had grown so large that its wrapping covered three market stalls",
        "guess": "the helpers had arranged the pieces in the wrong order",
        "clue": "the smallest label was tied to the largest bundle, while the heavy pieces all pointed toward the old bell tower",
        "truth": "the gift had been designed to unfold from the center, not from the outside",
        "failed": "pulling the outside ribbons only wrapped the stalls tighter",
        "jobs": "one measured the bundles, one read the labels aloud, and one cleared a safe path",
        "solution": "They placed the center piece first, stacked the lighter bundles above it, and tied one bright ribbon around the whole surprise",
        "ending": "When the final knot came loose, the enormous gift opened like a sunrise and made every child cheer",
        "measure": "the gift stood taller than the bell tower",
    },
    {
        "title": "the impossible picnic",
        "goal": "organize a gift picnic for a tired team of travelers",
        "problem": "the picnic basket was wider than the bridge and filled with enough food for a thousand people",
        "guess": "someone had confused the serving list with the shopping list",
        "clue": "the smallest basket held the guest list, but its numbers were written upside down",
        "truth": "the list had been read from the bottom upward, turning a small picnic into a giant one",
        "failed": "moving the biggest basket first made the bridge groan and sent napkins flying",
        "jobs": "one counted portions, one checked the names, and one carried only the foods that belonged to the first table",
        "solution": "They read the list in the proper order, sorted food by table, and saved the extra feast for the whole town",
        "ending": "The bridge stayed steady, and the surprise picnic fed every traveler beneath a sky full of kites",
        "measure": "the picnic basket could have sheltered a pony",
    },
    {
        "title": "the giant garden gift",
        "goal": "organize a thank-you gift for the town gardener",
        "problem": "a single flowerpot had grown into a garden large enough to swallow the town square",
        "guess": "the gardeners had planted every seed in one enormous row",
        "clue": "the tallest sunflowers leaned toward a hidden wooden sign beneath the leaves",
        "truth": "the gift was a living maze meant to be explored from the center outward",
        "failed": "cutting a straight path through the vines only made two more paths grow back",
        "jobs": "one marked the center, one tied gentle guide ribbons, and one evaluated each turn for safety",
        "solution": "They found the center, organized the paths by color, and placed the gift card beside the oldest rose",
        "ending": "The gardener entered the blooming maze and laughed when every flower seemed to clap",
        "measure": "the garden reached from the square to the far hill",
    },
]


@dataclass
class Entity:
    id: str
    kind: str
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    feature: str = "Happy Ending"


@dataclass
class Mood:
    hopeful: bool = True
    joyful: bool = False
    teamwork: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_kind: str
    helper_name: str
    helper_kind: str
    gift_type: str
    material: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mood: Mood) -> None:
        self.setting = setting
        self.mood = mood
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(line) for line in self.lines if line)


def tell(params: StoryParams) -> World:
    world = World(Setting(params.place), Mood())
    hero = world.add(Entity(params.hero_name, "character", params.hero_kind))
    helper = world.add(Entity(params.helper_name, "character", params.helper_kind))
    gift = world.add(Entity("gift", "present", params.gift_type, params.hero_name))
    rng = random.Random(params.seed if params.seed is not None else "|".join(vars(params).values().__str__()))
    tale = rng.choice(TALES)
    scale = rng.choice(
        [
            "so enormous that a sparrow needed a map to cross it",
            "large enough to cast a shadow over the noon parade",
            "so tall that clouds paused to admire it",
            "wide enough for a small wagon to turn around inside it",
        ]
    )
    evaluation = rng.choice(
        [
            "They tested each bundle gently before moving it.",
            "They measured every part twice and marked the safe pieces with chalk.",
            "They checked the balance, the labels, and the path before making another move.",
        ]
    )

    hero.meters["organizing_skill"] = 1.0
    hero.memes.update(hope=1.0, worry=1.0)
    helper.memes.update(curiosity=1.0, trust=1.0)
    gift.meters.update(size=10.0, safety=0.0)
    world.facts.update(tale=tale, hero=hero, helper=helper, gift=gift, scale=scale, evaluation=evaluation)

    world.say(
        f"In {params.place}, where ordinary umbrellas were used as roofs, {params.hero_name}, a remarkable {params.hero_kind}, announced a plan."
    )
    world.say(
        f'"We will organize {tale["goal"]}," {params.hero_name} said. "It will be the finest {params.gift_type} this town has ever seen."'
    )
    world.say(
        f"{params.helper_name}, a thoughtful {params.helper_kind}, looked at the {params.material} and blinked. The gift was {scale}."
    )
    world.para()
    world.say(f"The trouble was that {tale['problem']}.")
    world.say(f"{params.helper_name} whispered, \"Perhaps {tale['guess']}.\"")
    world.say(
        f'{params.hero_name} shook their head. "We should evaluate the clues before we blame the gift or the helpers."'
    )
    world.say(tale["failed"] + ".")
    world.say(f"Then they noticed that {tale['clue']}.")
    world.say(f"That clue revealed the truth: {tale['truth']}.")
    world.para()
    world.say(evaluation)
    world.say(
        f'"If we organize the work, the gift can still bring joy," said {params.helper_name}. "And I will help," replied {params.hero_name}.'
    )
    world.say(f"Together, {tale['jobs']}.")
    world.say(f"{tale['solution']}.")
    world.say(
        f"The gift was evaluated again: it was balanced, safe, and ready for its grand unveiling."
    )
    world.para()
    world.say(f"When the people gathered, {tale['ending']}.")
    world.say(
        f"{params.helper_name} smiled. \"The biggest part was not the size. It was how carefully we worked together.\""
    )
    world.say(
        f"{params.hero_name} tied the last {params.material} bow, and the whole town celebrated a happy ending beneath the shining sky."
    )

    hero.meters["organizing_skill"] = 2.0
    hero.memes.update(worry=0.0, confidence=1.0, joy=1.0)
    helper.memes.update(trust=2.0, joy=1.0)
    gift.meters.update(safety=1.0)
    world.mood.joyful = True
    return world


def generation_prompts(world: World) -> list[str]:
    tale = world.facts["tale"]
    return [
        "Write a child-friendly tall tale with a happy ending.",
        "Include a giant gift that must be organized and carefully evaluated.",
        f"Build the story around this goal: {tale['goal']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale = world.facts["tale"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    gift = world.facts["gift"]
    return [
        QAItem(
            f"Why did {hero.id} and {helper.id} need to organize the gift?",
            f"They needed to organize it because {tale['problem']}.",
        ),
        QAItem(
            "What clue helped them understand the gift?",
            f"They noticed that {tale['clue']}. This showed that {tale['truth']}.",
        ),
        QAItem(
            f"How did {hero.id} and {helper.id} evaluate the gift?",
            f"They checked its parts carefully, measured the bundles, and made sure it was balanced and safe before the unveiling.",
        ),
        QAItem(
            "What happened at the happy ending?",
            f"{tale['ending']}. The gift was ready because the team organized the work and evaluated the result.",
        ),
        QAItem(
            "What lesson did the tall tale show?",
            "A huge task becomes manageable when friends organize their work, examine clues, and help one another.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does organize mean?",
            "To organize means to arrange things in a clear order so they are easier to use or understand.",
        ),
        QAItem(
            "What is a gift?",
            "A gift is something given to someone to show kindness, care, or celebration.",
        ),
        QAItem(
            "What does evaluate mean?",
            "To evaluate means to examine something carefully and decide how well it works or how safe it is.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id} ({entity.kind}) meters={meters} memes={memes}"
        )
    lines.append(f"  feature={world.setting.feature} joyful={world.mood.joyful}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tall tale world about organizing and evaluating a giant gift."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--gift-type", choices=GIFT_TYPES)
    parser.add_argument("--seed", type=int, default=None)
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
    place = args.place or rng.choice(PLACES)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_choices = [name for name in HELPER_NAMES if name != hero_name]
    helper_name = args.helper_name or rng.choice(helper_choices)
    hero_kind = rng.choice(HERO_KINDS)
    helper_kind = rng.choice(HELPER_KINDS)
    gift_type = args.gift_type or rng.choice(GIFT_TYPES)
    material = rng.choice(MATERIALS)
    if hero_name == helper_name:
        raise StoryError("hero and helper must have different names")
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_kind=hero_kind,
        helper_name=helper_name,
        helper_kind=helper_kind,
        gift_type=gift_type,
        material=material,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    return "\n".join(
        [
            "domain(gift_tale).",
            "feature(happy_ending).",
            "action(organize).",
            "action(gift).",
            "action(evaluate).",
        ]
    )


ASP_RULES = r"""
valid_story :-
    domain(gift_tale),
    feature(happy_ending),
    action(organize),
    action(gift),
    action(evaluate).
#show valid_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/0."))
    values = set(asp.atoms(model, "valid_story"))
    expected = {()}
    if values == expected:
        params = StoryParams(
            place=PLACES[0],
            hero_name="Luna",
            hero_kind=HERO_KINDS[0],
            helper_name="Bram",
            helper_kind=HELPER_KINDS[0],
            gift_type=GIFT_TYPES[0],
            material=MATERIALS[0],
            seed=7,
        )
        sample = generate(params)
        required = ["organize", "gift", "evaluate"]
        if all(word in sample.story.lower() for word in required) and "happy ending" in sample.story.lower():
            print("OK: ASP facts and Python story agree.")
            return 0
        print("MISMATCH: generated story omitted required narrative instruments")
        return 1
    print("MISMATCH:", values, expected)
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise StoryError("-n must be at least 1")
    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed))
        params.seed = base_seed
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
            header=f"### story {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
