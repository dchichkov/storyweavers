#!/usr/bin/env python3
"""
A cheerful superhero quest about Luna, a grizzly, and the brave choice to
terminate a dangerous plan by scouring the forest for a kinder solution.
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
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    grizzly_name: str
    landmark: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Entity
    grizzly: Entity
    landmark: str
    quest_item: str
    danger: str
    plan: str
    search_complete: bool = False
    danger_terminated: bool = False
    friendship: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


HERO_NAMES = ["Luna", "Nova", "Mira", "Zara", "Pia", "Rin"]
GRIZZLY_NAMES = ["Bruno", "Tumble", "Honey", "Moss", "Bramble", "Gus"]
LANDMARKS = [
    "the Moonlit Mountain",
    "the Silver Pine Valley",
    "the Cloudberry Ridge",
    "the Starlight Forest",
    "the Whispering Canyon",
]
QUEST_ITEMS = [
    "a lost golden bell",
    "a blue lantern",
    "a singing compass",
    "a silver berry basket",
]
DANGERS = [
    "a runaway storm machine",
    "a spreading wall of thorny vines",
    "a rumbling rock gate",
    "a cloud of cold purple smoke",
]
PLANS = [
    "the old plan would have trapped the grizzly in a net",
    "the first plan would have blasted the vines apart",
    "the rushed idea would have sealed the grizzly inside the canyon",
    "the tempting shortcut would have sent the storm machine over the valley",
]
CLUES = [
    "tiny paw prints curved around the danger instead of toward it",
    "a feather caught on a low branch pointed toward a safer trail",
    "the grizzly's soft growl echoed from beneath a hollow tree",
    "three bright berries had been placed in a careful line beside the path",
]
SAFE_FIXES = [
    "rolled a fallen log beneath the lever so the machine could be stopped without harming anyone",
    "guided the vines toward a sunny stone garden where they could grow safely",
    "opened a narrow side passage and let the grizzly walk out on its own",
    "turned the lantern toward the smoke's hidden vent and closed it with a smooth river stone",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a happy superhero quest about Luna and a grizzly."
    )
    parser.add_argument("--hero-name", choices=HERO_NAMES)
    parser.add_argument("--grizzly-name", choices=GRIZZLY_NAMES)
    parser.add_argument("--landmark", choices=LANDMARKS)
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
    hero = args.hero_name or rng.choice(HERO_NAMES)
    choices = [name for name in GRIZZLY_NAMES if name != hero]
    grizzly = args.grizzly_name or rng.choice(choices)
    landmark = args.landmark or rng.choice(LANDMARKS)
    return StoryParams(hero_name=hero, grizzly_name=grizzly, landmark=landmark)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.grizzly_name:
        raise StoryError("The superhero and grizzly need different names.")
    if params.hero_name not in HERO_NAMES:
        raise StoryError("That hero name is not in Luna's superhero league.")
    if params.grizzly_name not in GRIZZLY_NAMES:
        raise StoryError("That grizzly name is not in the mountain rescue book.")
    if params.landmark not in LANDMARKS:
        raise StoryError("That landmark is outside the quest map.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)

    item = rng.choice(QUEST_ITEMS)
    danger = rng.choice(DANGERS)
    plan = rng.choice(PLANS)
    clue = rng.choice(CLUES)
    fix = rng.choice(SAFE_FIXES)
    opening = rng.choice([
        "At sunrise",
        "Just as the moon faded",
        "After breakfast",
        "One bright morning",
    ])
    power = rng.choice([
        "moonbeam vision",
        "a cape that could catch the wind",
        "super-hearing",
        "a silver rescue rope",
    ])
    thought = rng.choice([
        "I want to be fast, but a real hero must be careful first.",
        "I can terminate the danger without making a new danger.",
        "The answer may be hidden, so I will scour the trail before I act.",
        "A grizzly deserves a choice, not a frightening surprise.",
    ])
    ending = rng.choice([
        "the quest bell rang a warm golden note",
        "the lantern glowed like a tiny sunrise",
        "the valley filled with relieved cheers",
        "the grizzly danced beneath the first evening star",
    ])

    hero = Entity(
        params.hero_name,
        "superhero",
        meters={"distance_to_landmark": 12.0, "danger_level": 0.0},
        memes={"bravery": 1.0, "care": 1.0},
    )
    grizzly = Entity(
        params.grizzly_name,
        "grizzly",
        meters={"distance_to_landmark": 8.0, "danger_level": 0.0},
        memes={"caution": 1.0, "kindness": 1.0},
    )
    world = World(
        hero=hero,
        grizzly=grizzly,
        landmark=params.landmark,
        quest_item=item,
        danger=danger,
        plan=plan,
    )
    world.danger = danger
    world.facts["quest_item"] = item
    world.facts["clue"] = clue
    world.facts["safe_fix"] = fix

    lines = [
        f"{opening}, {params.hero_name} flew toward {params.landmark} with {power}.",
        f"A quest waited there: {item} had vanished while {danger} threatened the mountain path.",
        f"{params.grizzly_name}, a gentle grizzly with a worried rumble, stood beside the blocked trail.",
        f"{params.hero_name} nearly followed a hurried command, because {plan}.",
        f"Then the superhero paused and thought, \"{thought}\"",
        f"\"Are you hurt?\" {params.hero_name} asked.",
        f"\"No,\" said {params.grizzly_name}. \"I am trying to protect the little animals beyond the trail.\"",
        f"\"Then we will search together,\" replied {params.hero_name}. \"We will not guess.\"",
        f"Using careful eyes and listening ears, they scoured {params.landmark}.",
        f"They discovered the clue: {clue}.",
        f"{params.grizzly_name} tapped a safe path with one broad paw, and {params.hero_name} understood.",
        f"Together they {fix}.",
        f"The danger grew quiet, so {params.hero_name} could terminate the frightening plan without hurting the grizzly.",
        f"Behind a fern, the friends found {item}. {params.grizzly_name} carried it gently while the superhero cleared the trail.",
        f"At last, {ending}.",
        f"{params.grizzly_name} smiled, and {params.hero_name} smiled too. The quest had ended with courage, care, and a new friend.",
    ]

    world.search_complete = True
    world.danger_terminated = True
    world.friendship = True
    world.hero.meters["distance_to_landmark"] = 0.0
    world.hero.meters["danger_level"] = 0.0
    world.grizzly.meters["distance_to_landmark"] = 0.0
    world.grizzly.meters["danger_level"] = 0.0
    world.facts["ending"] = ending
    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Write a superhero quest in {params.landmark} where {params.hero_name} helps {params.grizzly_name}.",
        f"Tell a happy story about scouring {params.landmark}, finding {item}, and terminating a danger safely.",
        "Include an inner monologue, a brief dialogue exchange, and a kind heroic ending.",
    ]

    story_qa = [
        QAItem(
            question=f"What quest did {params.hero_name} undertake?",
            answer=f"{params.hero_name} searched {params.landmark} for {item} while protecting the mountain path from {danger}.",
        ),
        QAItem(
            question=f"Why did {params.hero_name} scour the landmark?",
            answer=f"{params.hero_name} scoured {params.landmark} to find a clue and a safe way to stop {danger}.",
        ),
        QAItem(
            question=f"What did {params.hero_name} think before acting?",
            answer=f"{params.hero_name} thought, \"{thought}\"",
        ),
        QAItem(
            question=f"How did the grizzly help?",
            answer=f"{params.grizzly_name} showed a safe path with a broad paw and explained that the animals beyond the trail needed protection.",
        ),
        QAItem(
            question="How did the story end happily?",
            answer=f"The friends found {item}, safely terminated the danger, cleared the trail, and celebrated together.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear. Even a gentle grizzly needs space, respect, and a safe way to choose where to go.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="To scour means to search a place carefully and thoroughly.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="To terminate means to bring something to an end. A careful hero should end a danger without creating a new one.",
        ),
        QAItem(
            question="What makes a superhero quest kind?",
            answer="A kind superhero quest protects people and animals, checks clues, listens to helpers, and chooses a safe solution.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thought written in the story so readers can understand the character's choice.",
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
        print("\n--- trace ---")
        print(
            f"hero={world.hero.name}, kind={world.hero.kind}, "
            f"meters={world.hero.meters}, memes={world.hero.memes}"
        )
        print(
            f"grizzly={world.grizzly.name}, kind={world.grizzly.kind}, "
            f"meters={world.grizzly.meters}, memes={world.grizzly.memes}"
        )
        print(
            f"landmark={world.landmark}, quest_item={world.quest_item}, "
            f"search_complete={world.search_complete}, "
            f"danger_terminated={world.danger_terminated}, friendship={world.friendship}"
        )
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
hero(H) :- hero_name(H).
grizzly(G) :- grizzly_name(G).
safe_quest(H,G) :- hero(H), grizzly(G), H != G.
quest_ready(H,G) :- safe_quest(H,G), search_method(scour), ending(happy).
can_terminate(H,G) :- quest_ready(H,G), protects(H,G).
#show valid_landmark/1.
valid_landmark(L) :- landmark(L).
"""


def asp_facts() -> str:
    import asp

    facts = []
    facts.extend(asp.fact("landmark", landmark) for landmark in LANDMARKS)
    facts.extend(asp.fact("hero_name", name) for name in HERO_NAMES)
    facts.extend(asp.fact("grizzly_name", name.lower()) for name in GRIZZLY_NAMES)
    facts.extend([
        asp.fact("search_method", "scour"),
        asp.fact("ending", "happy"),
        asp.fact("protects", "hero", "grizzly"),
    ])
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_landmarks() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_landmark/1."))
    return sorted(set(asp.atoms(model, "valid_landmark")))


def asp_verify() -> int:
    py = {(landmark,) for landmark in LANDMARKS}
    clingo_values = set(asp_valid_landmarks())
    if py == clingo_values:
        print(f"OK: clingo gate matches valid_landmarks() ({len(py)} landmarks).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - clingo_values:
        print("  only in python:", sorted(py - clingo_values))
    if clingo_values - py:
        print("  only in clingo:", sorted(clingo_values - py))
    return 1


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                grizzly_name=GRIZZLY_NAMES[index % len(GRIZZLY_NAMES)],
                landmark=landmark,
            )
            for index, landmark in enumerate(LANDMARKS)
        ]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [
        resolve_params(args, random.Random(base + index))
        for index in range(args.n)
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_landmark/1."))
        return
    if args.verify:
        status = asp_verify()
        if status == 0:
            for index, params in enumerate(generation_params(args)):
                params.seed = (args.seed if args.seed is not None else 0) + index
                sample = generate(params)
                if not sample.story or "happy" not in sample.story.lower():
                    print("Generation verification failed.")
                    sys.exit(1)
            print("OK: generated stories passed.")
        sys.exit(status)
    if args.asp:
        print("\n".join(value[0] for value in asp_valid_landmarks()))
        return

    samples = []
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
