#!/usr/bin/env python3
"""
A small slice-of-life storyworld about building with ivory, bacon, dialogue,
moral value, and a bad ending caused by a selfish choice.
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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = STORYWORLDS_ROOT.parent
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    builder: str
    helper: str
    place: str
    material: str
    food: str
    project: str
    seed: Optional[int] = None
    variant: int = 0


BUILDERS = ["Luna", "Mara", "Nia", "Tess", "Iris", "Wren"]
HELPERS = ["Pip", "Owen", "Bea", "Sam", "Jo", "Kai"]
PLACES = ["the apartment courtyard", "the little kitchen", "the community hall", "the back porch"]
PROJECTS = ["a small toy bridge", "a bird feeder", "a market stall", "a reading bench"]

SCENARIOS = [
    {
        "opening": "Luna found a smooth ivory tile beneath the old table.",
        "need": "The neighbors needed a small notice board before the afternoon market.",
        "plan": "Luna wanted to build its frame from the ivory pieces and paint the letters by hand.",
        "temptation": "Luna quietly kept the straightest ivory piece for a private box.",
        "bad": "The frame sagged because the missing piece left one corner weak, and the first rain blurred the notices.",
        "repair": "Luna returned the ivory piece, rebuilt the corner, and helped copy every wet notice.",
        "lesson": "A beautiful material has little value when it is kept from the work that needs it.",
        "ending": "By evening, the repaired board stood square beside a plate of crisp bacon.",
    },
    {
        "opening": "A pale ivory button rolled under Luna's chair during breakfast.",
        "need": "The neighbors were building a little puppet theater for the children.",
        "plan": "Luna planned to use the ivory button as a bright moon above the stage.",
        "temptation": "Luna took two matching buttons for a coat instead.",
        "bad": "The theater had no moon, and its curtain pulled loose when the children tried to play.",
        "repair": "Luna gave back the buttons, stitched the curtain, and made the moon shine above the stage.",
        "lesson": "A small selfish choice can dim something that many people hoped to enjoy.",
        "ending": "The last puppet bowed while bacon sizzled in the nearby kitchen.",
    },
    {
        "opening": "Luna noticed an ivory-colored peg missing from the shared tool shelf.",
        "need": "The neighbors were building a rack for their garden baskets.",
        "plan": "Luna meant to use the peg to hold the rack's top rail steady.",
        "temptation": "Luna hid the peg in a drawer so nobody else could use it.",
        "bad": "The rack tipped during lunch, spilling carrots and making the garden work harder.",
        "repair": "Luna fetched the peg, strengthened the rack, and gathered the scattered vegetables.",
        "lesson": "Useful things should be shared fairly, especially when many hands depend on them.",
        "ending": "The sturdy rack held its baskets while bacon cooled on a paper plate.",
    },
]

OPENINGS = [
    "{opening} In {place}, {builder} had promised to build something useful.",
    "On an ordinary morning in {place}, {builder} began a careful build.",
    "{builder} set out boards and string in {place}, hoping to make a kind thing for everyone.",
]

DIALOGUE = [
    '"That ivory piece belongs in the build," {helper} said. "It will make the corner strong."',
    '"Could we share it?" {helper} asked. "The project is for all of us."',
    '"I only wanted one special thing," {builder} admitted. "{helper}, I see what my choice changed."',
]

@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A slice-of-life building storyworld.")
    parser.add_argument("--builder")
    parser.add_argument("--helper")
    parser.add_argument("--place")
    parser.add_argument("--material")
    parser.add_argument("--food")
    parser.add_argument("--project")
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


def generate_world(params: StoryParams) -> World:
    if params.material.casefold() != "ivory":
        raise StoryError("This domain requires ivory as the building material.")
    if params.food.casefold() != "bacon":
        raise StoryError("This domain requires bacon as the shared food.")
    if params.builder.casefold() == params.helper.casefold():
        raise StoryError("The builder and helper must be different people.")

    world = World(params.place)
    world.add(Entity("builder", "character", params.builder, memes={"honesty": 0.3}))
    world.add(Entity("helper", "character", params.helper, memes={"fairness": 0.6}))
    world.add(Entity("material", "thing", params.material, owner="neighbors", meters={"pieces": 3}))
    world.add(Entity("food", "thing", params.food, owner="neighbors", meters={"servings": 4}))
    world.add(Entity("project", "thing", params.project, owner="neighbors"))
    return world


def tell(world: World, params: StoryParams) -> None:
    rng = random.Random((params.seed or 0) ^ params.variant ^ 0xBACE)
    scenario = SCENARIOS[params.variant % len(SCENARIOS)]
    builder = params.builder
    helper = params.helper

    paragraphs = [
        rng.choice(OPENINGS).format(
            opening=scenario["opening"],
            place=params.place,
            builder=builder,
        ),
        scenario["need"],
        scenario["plan"],
        f'{builder} measured the boards twice. Nearby, someone was frying {params.food}.',
        f'{builder} thought, "{scenario["temptation"]}"',
        f'{helper} arrived with a cup of water and noticed the missing piece. {DIALOGUE[0].format(helper=helper)}',
        f'{builder} looked away. "I thought nobody would mind," {builder} said.',
        f'{helper} answered, "People will mind when the build cannot serve them."',
        f'{builder} continued without asking for help. Then the bad ending arrived: {scenario["bad"]}',
        f'{helper} said, "{scenario["lesson"]}"',
        f'{builder} took a breath. {DIALOGUE[2].format(builder=builder, helper=helper)}',
        f'Together, they {scenario["repair"]}',
        f'{scenario["lesson"]} The moral value was not in owning ivory, but in using what was shared with care.',
        scenario["ending"],
    ]
    world.facts = {
        "builder": builder,
        "helper": helper,
        "place": params.place,
        "material": params.material,
        "food": params.food,
        "project": params.project,
        "need": scenario["need"],
        "plan": scenario["plan"],
        "temptation": scenario["temptation"],
        "bad": scenario["bad"],
        "repair": scenario["repair"],
        "lesson": scenario["lesson"],
        "ending": scenario["ending"],
        "story": "\n\n".join(paragraphs),
    }
    world.entities["builder"].memes["honesty"] = 1.0
    world.entities["helper"].memes["fairness"] = 1.0
    world.entities["material"].meters["pieces"] = 3
    world.fired.update({"selfish_choice", "bad_ending", "repair_completed"})


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    tell(world, params)
    f = world.facts
    return StorySample(
        params=params,
        story=f["story"],
        prompts=[
            f"Write a slice-of-life story about {f['builder']} building {f['project']} with {f['material']}.",
            f"Include bacon, dialogue, a bad ending, and the moral value: {f['lesson']}",
        ],
        story_qa=[
            QAItem("Who was building the project?", f"{f['builder']} was building {f['project']}."),
            QAItem("What material was part of the build?", f"The build used {f['material']}."),
            QAItem("What went wrong?", f"{f['bad']}"),
            QAItem("How did the helper change the builder's thinking?", f'{f["helper"]} explained that the shared material had to serve the neighbors, so {f["builder"]} repaired the build.'),
            QAItem("What moral value did the story show?", f"The story showed fairness and honesty: {f['lesson']}"),
            QAItem("What food was nearby?", f"{f['food'].capitalize()} was being cooked nearby."),
        ],
        world_qa=[
            QAItem("Why is sharing valuable?", "Sharing lets a useful thing help more people instead of serving only one person's private wish."),
            QAItem("What is a bad ending?", "A bad ending is an outcome in which a poor choice causes harm or disappointment before the lesson is understood."),
            QAItem("What is dialogue?", "Dialogue is spoken conversation between characters that can reveal feelings and change what they do."),
            QAItem("What is ivory?", "Ivory is a hard, pale material; in this story it is treated as a scarce shared building material."),
        ],
        world=world,
    )


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("material", "ivory"),
        asp.fact("food", "bacon"),
        asp.fact("value", "sharing"),
        asp.fact("outcome", "bad_ending"),
    ])


ASP_RULES = r"""
needed_material(ivory).
shared_food(bacon).
moral_value(sharing).
bad_choice(hoarding).
bad_ending :- bad_choice(hoarding), needed_material(ivory).
repair_possible :- bad_ending, moral_value(sharing).
#show bad_ending/0.
#show repair_possible/0.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    atoms = {str(symbol) for symbol in model}
    expected = {"bad_ending", "repair_possible"}
    if expected.issubset(atoms):
        print("OK: ASP model contains the bad ending and possible repair.")
        return 0
    print("ASP verification failed.")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== Generation prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams("Luna", "Pip", "the apartment courtyard", "ivory", "bacon", "a small toy bridge", 11, 0),
    StoryParams("Mara", "Owen", "the little kitchen", "ivory", "bacon", "a bird feeder", 29, 1),
    StoryParams("Nia", "Bea", "the community hall", "ivory", "bacon", "a reading bench", 47, 2),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    builder = args.builder or rng.choice(BUILDERS)
    choices = [name for name in HELPERS if name != builder]
    return StoryParams(
        builder=builder,
        helper=args.helper or rng.choice(choices),
        place=args.place or rng.choice(PLACES),
        material=args.material or "ivory",
        food=args.food or "bacon",
        project=args.project or rng.choice(PROJECTS),
        seed=None,
        variant=rng.randrange(1_000_000_000),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
