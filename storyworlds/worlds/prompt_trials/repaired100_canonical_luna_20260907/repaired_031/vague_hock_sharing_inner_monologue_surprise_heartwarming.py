#!/usr/bin/env python3
"""
Standalone story world: a vague clue, a sore hock, and a shared surprise.

Luna notices a small animal hiding a sore hock near a community garden. A vague
clue leads her and a helper to discover that the animal needs a quiet place and
a shared snack. Luna's private thoughts guide her choices, while a gentle
surprise brings the neighbors together.
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
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Place:
    id: str
    label: str
    features: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    owner: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.kind == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    helper_name: str
    animal: str
    clue_variant: int = 0
    sharing_variant: int = 0
    surprise_variant: int = 0
    seed: Optional[int] = None


PLACES = {
    "community_garden": Place(
        "community_garden",
        "the community garden",
        {"raised_beds", "bench", "shared_lunch"},
    ),
    "orchard_path": Place(
        "orchard_path",
        "the orchard path",
        {"apple_trees", "stone_wall", "shared_lunch"},
    ),
    "school_courtyard": Place(
        "school_courtyard",
        "the school courtyard",
        {"planters", "quiet_corner", "shared_lunch"},
    ),
}

ANIMALS = {
    "goat": {
        "label": "a little goat",
        "name": "Nettle",
        "food": "crisp apple slices",
        "sound": "a soft maa",
    },
    "lamb": {
        "label": "a young lamb",
        "name": "Cloud",
        "food": "tender clover",
        "sound": "a small baa",
    },
    "pony": {
        "label": "a small pony",
        "name": "Button",
        "food": "sweet carrot coins",
        "sound": "a quiet nicker",
    },
}

GIRL_NAMES = ["Luna", "Mira", "Nora", "Ivy"]
BOY_NAMES = ["Theo", "Milo", "Eli", "Owen"]
HELPERS = ["Grandma", "Dad", "Aunt May", "Mr. Rowan"]

CLUE_VARIANTS = [
    "Near the gate, Luna noticed a vague trail of bent grass and one shining button.",
    "A vague little scrape beside the path made Luna stop and listen.",
    "Someone had left a vague message in the dirt: one arrow, one dot, and no words.",
    "Luna heard a vague rustle behind the bench, then saw a single green leaf tremble.",
]

SHARING_VARIANTS = [
    "Luna divided the lunch into tiny portions instead of keeping the best pieces for herself.",
    "She offered the animal a quiet corner and shared each apple slice with the children who had gathered.",
    "Luna asked everyone to make a circle, leaving the middle open and the food easy to reach.",
    "She placed the food near the shade, then invited the others to share their stories while the animal rested.",
]

SURPRISE_VARIANTS = [
    "When the animal finally stepped into the sun, the children revealed a paper garland made from leaves.",
    "The surprise was not a loud cheer but a row of painted signs saying, “You are safe here.”",
    "A gardener returned with a tiny blue blanket, sewn from scraps that each neighbor had shared.",
    "The animal's owner appeared with a grateful smile, carrying a bell that chimed only when touched softly.",
]


def valid_combo(place: str, animal: str) -> bool:
    return place in PLACES and animal in ANIMALS


def explain_rejection(place: str, animal: str) -> str:
    return (
        f"No story: {place!r} and {animal!r} do not form a supported setting "
        "and animal combination."
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    animal = args.animal or rng.choice(list(ANIMALS))
    if not valid_combo(place, animal):
        raise StoryError(explain_rejection(place, animal))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(
        place=place,
        child_name=name,
        child_gender=gender,
        helper_name=helper,
        animal=animal,
        clue_variant=rng.randrange(len(CLUE_VARIANTS)),
        sharing_variant=rng.randrange(len(SHARING_VARIANTS)),
        surprise_variant=rng.randrange(len(SURPRISE_VARIANTS)),
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    animal_data = ANIMALS[params.animal]
    world = World(place)

    child = world.add(
        Entity(
            params.child_name,
            params.child_gender,
            params.child_name,
            ["observant", "generous"],
        )
    )
    helper = world.add(
        Entity(params.helper_name, "adult", params.helper_name, ["patient"])
    )
    animal = world.add(
        Entity(
            animal_data["name"],
            "animal",
            animal_data["label"],
            ["gentle", "hurt", "shy"],
        )
    )

    child.memes["curiosity"] = 1.0
    child.memes["generosity"] = 1.0
    animal.meters["hock_pain"] = 1.0
    animal.memes["fear"] = 1.0

    world.facts.update(
        child=child,
        helper=helper,
        animal=animal,
        animal_data=animal_data,
        place=place,
    )

    world.say(
        f"{child.label} visited {place.label} with {helper.label}, carrying a small basket for everyone."
    )
    world.say(
        f"The morning was bright, but {child.label} felt that something was missing from the cheerful garden."
    )
    world.para()

    world.say(CLUE_VARIANTS[params.clue_variant % len(CLUE_VARIANTS)])
    world.say(
        f"Behind the bench, {child.label} found {animal.label} resting with one hock held carefully off the ground."
    )
    world.facts["vague_clue"] = True
    world.facts["injury"] = "sore hock"
    world.say(
        f"Inside {child.pronoun('possessive')} thoughts, {child.label} wondered, "
        "“Is it frightened, hungry, or hurt? I should look gently before I guess.”"
    )

    world.para()
    world.say(
        f'{helper.label} whispered, “What do you see?” {child.label} answered, '
        f'“A sore hock and a worried face. Let us give {animal.label} space.”'
    )
    world.say(
        f"{helper.label} nodded. “Good noticing. We can help without crowding it.”"
    )
    world.say(
        f"{child.label} {SHARING_VARIANTS[params.sharing_variant % len(SHARING_VARIANTS)]}"
    )
    world.fired.add("share_food")
    child.memes["generosity"] += 1.0
    animal.memes["trust"] = 1.0
    animal.memes["fear"] = 0.4
    world.say(
        f"The animal followed the quiet scent, took one bite, and rested its sore hock on the soft blanket."
    )

    world.para()
    world.say(
        f"Then came a gentle surprise: {SURPRISE_VARIANTS[params.surprise_variant % len(SURPRISE_VARIANTS)]}"
    )
    world.say(
        f"{child.label} smiled. “We did not need to know everything at once. We only needed to notice and share.”"
    )
    world.say(
        f"{helper.label} replied, “That is how a small kindness finds its way around a whole place.”"
    )
    world.fired.add("surprise")
    animal.meters["hock_pain"] = 0.3
    animal.memes["trust"] = 1.0
    animal.memes["calm"] = 1.0
    world.facts["resolved"] = True

    world.para()
    world.say(
        f"By lunchtime, {animal.label} was still careful, but it was no longer alone. "
        f"It made {animal_data['sound']} while the neighbors shared the last of the basket."
    )
    world.say(
        f"{child.label} tucked the vague clue into a little story for later, "
        "remembering that kindness can begin before the whole answer is clear."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a heartwarming child-friendly story about sharing food with a shy animal that has a sore hock.",
        f"Use a vague clue to show how {f['child'].label} notices that {f['animal'].label} needs help.",
        "Include inner monologue, a brief dialogue exchange, and a gentle surprise that brings people together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    animal = f["animal"]
    helper = f["helper"]
    return [
        QAItem(
            f"What vague clue did {child.label} notice?",
            f"{child.label} noticed a vague sign near the path and then found {animal.label} resting with a sore hock.",
        ),
        QAItem(
            f"Why was {animal.label} hiding?",
            f"{animal.label} was hiding because its hock was sore, so it was frightened and needed a calm place to rest.",
        ),
        QAItem(
            f"How did {child.label} and {helper.label} help?",
            f"They gave {animal.label} space, shared food, and made a soft place where it could rest without being crowded.",
        ),
        QAItem(
            "What was the surprise?",
            f"{SURPRISE_VARIANTS[world.facts['params'].surprise_variant] if 'params' in world.facts else 'The neighbors prepared a gentle welcome.'}",
        ),
        QAItem(
            "What changed by the end?",
            f"The animal was still careful, but its fear had eased, its sore hock was supported, and it was no longer alone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a hock?",
            "A hock is a joint in the lower part of an animal's back leg, somewhat like a heel and ankle together.",
        ),
        QAItem(
            "Why is sharing helpful?",
            "Sharing can make sure that someone who needs food, space, or comfort does not have to face a difficult moment alone.",
        ),
        QAItem(
            "What does vague mean?",
            "Vague means not fully clear or exact, like a clue that gives only a small hint.",
        ),
        QAItem(
            "Why should people move gently around an injured animal?",
            "Gentle movements help an injured animal feel safer and avoid extra pain or fear.",
        ),
        QAItem(
            "What is a surprise?",
            "A surprise is something unexpected that a person discovers or receives.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
injured(A) :- animal(A), sore_hock(A).
can_help(C, A) :- child(C), animal(A), injured(A), shares_food(C).
good_story(P, C, A) :- place(P), child(C), animal(A), can_help(C, A), surprise(P).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
        lines.append(asp.fact("surprise", place))
    lines.append(asp.fact("child", "child"))
    for animal in ANIMALS:
        lines.append(asp.fact("animal", animal))
        lines.append(asp.fact("sore_hock", animal))
    lines.append(asp.fact("shares_food", "child"))
    return "\n".join(lines)


def asp_program(show: str = "#show good_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = sorted(
        (place, "child", animal)
        for place in PLACES
        for animal in ANIMALS
        if valid_combo(place, animal)
    )
    clingo_rows = asp_valid_combos()
    if py == clingo_rows:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("python:", py)
    print("clingo:", clingo_rows)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    world.facts["params"] = params
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.label}: kind={entity.kind}, meters={meters}, memes={memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming story world about a vague clue, a sore hock, and sharing."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--animal", choices=sorted(ANIMALS))
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--gender", choices=["girl", "boy"])
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


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("community_garden", "Luna", "girl", "Grandma", "goat", 0, 0, 0),
        StoryParams("orchard_path", "Theo", "boy", "Dad", "pony", 1, 1, 1),
        StoryParams("school_courtyard", "Mira", "girl", "Aunt May", "lamb", 2, 2, 2),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in curated_params()]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = (
                f"### {sample.params.child_name}: "
                f"{sample.params.animal} at {sample.params.place}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
