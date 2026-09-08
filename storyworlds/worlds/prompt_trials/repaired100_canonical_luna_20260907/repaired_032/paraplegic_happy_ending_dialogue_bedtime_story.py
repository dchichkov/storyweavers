#!/usr/bin/env python3
"""
A gentle bedtime storyworld about Luna, a paraplegic child, a moonlit garden,
and a little lantern whose safe return brings friends together.
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    features: set[str] = field(default_factory=set)


@dataclass
class PathPlan:
    id: str
    surface: str
    gentle: bool
    route: str
    ending_image: str


@dataclass
class StoryParams:
    place: str
    plan: str
    name: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "moon_garden": Place(
        "moon_garden",
        "the moon garden behind Luna's house",
        {"flowers", "lantern_hook", "smooth_path"},
    ),
    "quiet_terrace": Place(
        "quiet_terrace",
        "the quiet terrace above the sleeping town",
        {"flowers", "lantern_hook", "smooth_path"},
    ),
    "willow_yard": Place(
        "willow_yard",
        "the willow yard beside the little pond",
        {"flowers", "lantern_hook", "smooth_path"},
    ),
}

PLANS = {
    "stone_path": PathPlan(
        "stone_path",
        "flat stepping stones",
        True,
        "the wide stone path around the flower beds",
        "the lantern glowed above the path like a tiny moon that had learned to smile",
    ),
    "wooden_boardwalk": PathPlan(
        "wooden_boardwalk",
        "a firm wooden boardwalk",
        True,
        "the level boardwalk beneath the willow branches",
        "the lantern shone along the boards, and the pond answered with a trail of gold",
    ),
    "garden_mat": PathPlan(
        "garden_mat",
        "a broad woven garden mat",
        True,
        "the smooth mat laid across the soft grass",
        "the lantern made the mat look like a golden road leading gently into a dream",
    ),
}

NAMES = ["Luna", "Mira", "Nora", "Tessa", "Iris"]
HELPERS = ["Ari", "Theo", "Sam", "Milo", "Jun"]
NAME_TYPES = {
    "Luna": "girl",
    "Mira": "girl",
    "Nora": "girl",
    "Tessa": "girl",
    "Iris": "girl",
    "Ari": "child",
    "Theo": "boy",
    "Sam": "child",
    "Milo": "boy",
    "Jun": "child",
}

ASP_RULES = r"""
place(P) :- place_name(P).
plan(R) :- plan_name(R).

safe_plan(R) :- plan(R), gentle(R), stable(R).
valid_story(P, R) :- place(P), safe_plan(R), has_feature(P, smooth_path).

#show valid_story/2.
"""


def valid_combos() -> list[tuple[str, str]]:
    return [
        (place_id, plan_id)
        for place_id, place in PLACES.items()
        for plan_id, plan in PLANS.items()
        if "smooth_path" in place.features and plan.gentle
    ]


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place_name", pid))
        for feature in sorted(place.features):
            lines.append(asp.fact("has_feature", pid, feature))
    for rid, plan in PLANS.items():
        lines.append(asp.fact("plan_name", rid))
        if plan.gentle:
            lines.append(asp.fact("gentle", rid))
        lines.append(asp.fact("stable", rid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_combos = set(asp_valid_stories())
    if py == clingo_combos:
        print(f"OK: clingo gate matches Python ({len(py)} valid combinations).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in clingo:", sorted(clingo_combos - py))
    print("  only in Python:", sorted(py - clingo_combos))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bedtime storyworld about Luna, a paraplegic child, and a moon lantern."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--plan", choices=sorted(PLANS))
    parser.add_argument("--name")
    parser.add_argument("--helper")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        combo
        for combo in valid_combos()
        if args.place is None or combo[0] == args.place
        if args.plan is None or combo[1] == args.plan
    ]
    if not choices:
        raise StoryError("No safe place and path plan match the requested options.")
    place, plan = rng.choice(sorted(choices))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([item for item in HELPERS if item != name])
    if helper == name:
        raise StoryError("The helper must be a different character from the storyteller.")
    return StoryParams(place=place, plan=plan, name=name, helper=helper)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    plan = PLANS[params.plan]
    world = World(place)

    luna = world.add(
        Entity(
            params.name,
            "character",
            params.name,
            NAME_TYPES.get(params.name, "child"),
            meters={"mobility": 1.0, "distance_to_lantern": 3.0},
            memes={"patience": 1.0, "hope": 1.0},
        )
    )
    helper = world.add(
        Entity(
            params.helper,
            "character",
            params.helper,
            NAME_TYPES.get(params.helper, "child"),
            meters={"mobility": 1.0},
            memes={"kindness": 1.0, "listening": 1.0},
        )
    )
    lantern = world.add(
        Entity(
            "moon_lantern",
            "object",
            "the moon lantern",
            meters={"light": 1.0, "height": 1.0},
            memes={"belonging": 0.0},
        )
    )
    bell = world.add(
        Entity(
            "bedtime_bell",
            "object",
            "the bedtime bell",
            meters={"sound": 1.0},
            memes={"welcome": 1.0},
        )
    )

    world.facts.update(
        luna=luna,
        helper=helper,
        lantern=lantern,
        bell=bell,
        plan=plan,
        safe_route=plan.route,
        resolved=False,
        dialogue_changed=True,
    )
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    luna: Entity = world.facts["luna"]
    helper: Entity = world.facts["helper"]
    lantern: Entity = world.facts["lantern"]
    bell: Entity = world.facts["bell"]
    plan: PathPlan = world.facts["plan"]
    place = world.place

    world.say(
        f"At bedtime, {luna.label}, a paraplegic child who loved the night sky, "
        f"rolled quietly toward {place.label}."
    )
    world.say(
        f"The garden was hushed, and {lantern.label} waited beside its hook while "
        f"the first stars blinked awake."
    )
    world.say(
        f"Then a soft wind loosened the lantern, and it rested just beyond "
        f"{plan.route}."
    )

    world.para()
    world.say(f"\"I want to bring it back safely,\" said {luna.label}.")
    world.say(
        f"\"Tell me what would help,\" answered {helper.label}. "
        f"\"I will listen, and we can make a plan together.\""
    )
    world.say(
        f"{luna.label} looked carefully at {plan.surface} and replied, "
        f"\"That route is firm and gentle. Please place the lantern within reach, "
        f"and I will guide it home.\""
    )
    world.say(
        f"{helper.label} nodded, moved slowly along {plan.route}, and held the "
        f"lantern steady instead of rushing."
    )

    luna.memes["hope"] += 1.0
    helper.memes["listening"] += 1.0
    lantern.memes["belonging"] += 1.0
    lantern.meters["distance_to_hook"] = 0.0
    world.fired.add("safe_teamwork")

    world.para()
    world.say(
        f"Together they returned {lantern.label} to its hook, where its warm light "
        f"spread across the flowers."
    )
    world.say(
        f"\"You listened to my plan,\" said {luna.label}. "
        f"\"That made the whole garden feel possible.\""
    )
    world.say(
        f"\"And you showed me that asking for the right help is part of being brave,\" "
        f"said {helper.label}."
    )
    world.say(
        f"The {bell.label} gave one tiny chime. {plan.ending_image.capitalize()}."
    )
    world.say(
        f"Under that friendly light, {luna.label} and {helper.label} went inside, "
        f"ready for a peaceful sleep."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    luna: Entity = world.facts["luna"]
    helper: Entity = world.facts["helper"]
    plan: PathPlan = world.facts["plan"]
    return [
        "Write a gentle bedtime story with a happy ending and warm dialogue.",
        f"Tell how {luna.label}, a paraplegic child, solves a small nighttime problem with {helper.label}.",
        f"Include a safe, accessible route using {plan.surface}, and let the characters' conversation change their plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    luna: Entity = world.facts["luna"]
    helper: Entity = world.facts["helper"]
    plan: PathPlan = world.facts["plan"]
    return [
        QAItem(
            question=f"What did {luna.label} notice in the garden?",
            answer=f"{luna.label} noticed that the moon lantern had come loose and was resting beyond {plan.route}.",
        ),
        QAItem(
            question=f"How did {helper.label} help {luna.label}?",
            answer=f"{helper.label} listened to {luna.label}'s plan, used the firm route, and held the lantern steady so it could be returned safely.",
        ),
        QAItem(
            question="How did the dialogue change what happened?",
            answer=f"{luna.label} explained which route was gentle and what help was needed, so {helper.label} followed that plan instead of rushing.",
        ),
        QAItem(
            question="Why was the route important?",
            answer=f"The route was important because it was made from {plan.surface} and gave the children a safe, careful way to bring the lantern home.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They returned the lantern to its hook, heard the bedtime bell chime, and went inside peacefully beneath the warm garden light.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does paraplegic mean?",
            answer="Paraplegic describes a person who has paralysis affecting the lower part of the body; people may use wheelchairs and other tools in different ways.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is an ending in which the main problem is solved and the characters are safe, comforted, or glad.",
        ),
        QAItem(
            question="Why is dialogue useful in a story?",
            answer="Dialogue lets characters share ideas and feelings, and their words can change what they decide or do.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  place: {world.place.label}")
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: type={entity.type}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  fired: {sorted(world.fired)}")
    lines.append(f"  resolved: {world.facts.get('resolved')}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(
        place="moon_garden",
        plan="stone_path",
        name="Luna",
        helper="Ari",
    ),
    StoryParams(
        place="quiet_terrace",
        plan="wooden_boardwalk",
        name="Mira",
        helper="Theo",
    ),
    StoryParams(
        place="willow_yard",
        plan="garden_mat",
        name="Nora",
        helper="Sam",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid place and path combinations:")
        for item in stories:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            attempts += 1
            try:
                params = resolve_params(args, random.Random(base_seed + attempts))
            except StoryError as error:
                print(error)
                return
            params.seed = base_seed + attempts
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
