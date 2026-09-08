#!/usr/bin/env python3
"""
A small animal storyworld about Chef Basil and a morbid mistake that receives
a bad ending. The story stays child-facing: the danger is a failed plan and
spoiled supper, not harm to an animal.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Recipe:
    id: str
    dish: str
    ingredient: str
    animal: str
    clue: str
    mistake: str
    consequence: str
    dialogue: str
    repair: str
    ending: str


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


RECIPES = {
    "berry_pie": Recipe(
        "berry_pie",
        "berry pie",
        "red berries",
        "hedgehog",
        "The hedgehog was carrying the berries to its winter basket.",
        "Chef Basil scooped the berries away before asking where they came from.",
        "The pie turned sour, and the hedgehog's basket stayed empty.",
        '"Those were not spare berries," said the hedgehog. "They were my winter food."',
        "Chef Basil returned the berries he could find, baked a plain oat cake instead, and labeled every bowl.",
        "The bad pie sat untouched in the compost pail while the hedgehog guarded a full basket.",
    ),
    "carrot_soup": Recipe(
        "carrot_soup",
        "carrot soup",
        "orange carrots",
        "rabbit",
        "The rabbit had tied green ribbons around the carrots in its garden row.",
        "Chef Basil pulled the ribboned carrots without checking the garden sign.",
        "The soup tasted bitter, and the rabbit's garden lost its best row.",
        '"Please read the sign," said the rabbit. "Those carrots were for my seed show."',
        "Chef Basil replanted the loose tops, apologized, and made a soup from the marked pantry carrots.",
        "The bitter soup cooled by the stove while the rabbit displayed its rescued garden row.",
    ),
    "apple_crumble": Recipe(
        "apple_crumble",
        "apple crumble",
        "striped apples",
        "squirrel",
        "The squirrel had painted stripes on the apples it was saving for a family picnic.",
        "Chef Basil mistook the painted apples for a pantry decoration and chopped them all.",
        "The crumble burned because the apples were too small and dry.",
        '"My picnic apples!" cried the squirrel. "You should have asked."',
        "Chef Basil carried fresh apples from the market and helped the squirrel plan a new picnic.",
        "The burned crumble became a sad black heap, while the squirrel shared a fresh apple under the oak.",
    ),
    "corn_muffins": Recipe(
        "corn_muffins",
        "corn muffins",
        "golden corn",
        "mouse",
        "The mouse had stacked the corn in tiny towers beside the mill.",
        "Chef Basil swept the towers into a bowl without noticing the mouse's measuring marks.",
        "The muffins rose unevenly and collapsed into heavy lumps.",
        '"Those marks showed my recipe," said the mouse. "You swept away the instructions."',
        "Chef Basil measured a new batch slowly and placed a small sign beside the mouse's towers.",
        "The first batch stayed lumpy on the cooling rack while the mouse watched the careful second batch rise.",
    ),
    "pumpkin_stew": Recipe(
        "pumpkin_stew",
        "pumpkin stew",
        "small pumpkins",
        "goat",
        "The goat had chosen the smallest pumpkins for a lantern contest.",
        "Chef Basil cut them open before seeing the painted contest numbers.",
        "The stew was watery, and the contest pumpkins could not become lanterns.",
        '"Those numbers mattered," said the goat. "A chef must notice before cutting."',
        "Chef Basil found one uncut pumpkin for the contest and wrote a harvest list for the kitchen.",
        "The watery stew filled one lonely bowl while the goat lit its single rescued pumpkin.",
    ),
    "honey_biscuits": Recipe(
        "honey_biscuits",
        "honey biscuits",
        "a jar of honey",
        "bee",
        "The bee had placed a blue ribbon on a jar reserved for the hive's winter stores.",
        "Chef Basil poured from the ribboned jar without checking the label.",
        "The biscuits came out hard, and the hive's winter jar was nearly empty.",
        '"That honey was marked," buzzed the bee. "A ribbon is a message."',
        "Chef Basil baked unsweetened biscuits, returned the jar, and made a clear shelf label.",
        "The hard biscuits cracked in the basket while the bee carried the protected jar home.",
    ),
}

NAMES = ["Basil", "Mara", "Pip", "Nell", "Toby", "Luca"]
ROLES = ["young chef", "apprentice chef", "careful chef"]
OPENINGS = [
    "At sunrise",
    "Before the market opened",
    "On a bright kitchen morning",
    "While the meadow was still damp",
    "Just before lunch",
]
LESSONS = [
    "A chef must ask before taking what belongs to another creature.",
    "A quick hand can make a bad ending from a simple mistake.",
    "Labels, signs, and questions can protect both food and friends.",
    "Good cooking begins with noticing.",
]


@dataclass
class StoryParams:
    recipe: str
    name: str
    role: str
    opening: int = 0
    lesson: int = 0
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    recipe = RECIPES[params.recipe]
    world = World()
    chef = world.add(Entity("chef", "character", params.name))
    animal = world.add(Entity("animal", "animal", recipe.animal))
    ingredient = world.add(Entity("ingredient", "food", recipe.ingredient))
    pot = world.add(Entity("pot", "object", recipe.dish))
    world.facts.update(
        chef=chef,
        animal=animal,
        ingredient=ingredient,
        pot=pot,
        recipe=recipe,
        lesson=LESSONS[params.lesson % len(LESSONS)],
        bad_ending=True,
    )

    world.say(
        f"{OPENINGS[params.opening % len(OPENINGS)]}, {params.name}, a {params.role}, "
        f"opened the little animal kitchen beside the meadow."
    )
    world.say(
        f"Chef {params.name} planned to make {recipe.dish} with {recipe.ingredient}. "
        f"{recipe.clue}"
    )
    world.say(
        f'The {recipe.animal} waved, but Chef {params.name} was hurrying. '
        f'"I can cook this quickly," said Chef {params.name}.'
    )
    world.para()
    world.say(recipe.mistake)
    world.say(f"The {recipe.animal} hurried after the chef and called, {recipe.dialogue}")
    world.say(recipe.consequence)
    chef.meters.update({"hurry": 1.0, "care": 0.0, "regret": 1.0})
    animal.memes.update({"sadness": 1.0, "trust": -1.0})
    pot.meters["spoiled"] = 1.0
    world.fired.update({"taken_without_asking", "bad_ending"})
    world.para()
    world.say(
        f"Chef {params.name} put down the spoon. "
        f'"You are right. I hurried past the clue, and I made a morbidly poor choice for a friendly kitchen," '
        f"said Chef {params.name}."
    )
    world.say(recipe.repair)
    chef.meters.update({"hurry": 0.0, "care": 1.0, "regret": 0.5})
    animal.memes.update({"sadness": 0.5, "trust": 0.5})
    world.fired.add("repair_attempt")
    world.say(
        f"The {recipe.animal} accepted the help, but the first dish could not be saved. "
        f"{recipe.ending}"
    )
    world.say(
        f"Chef {params.name} wrote the lesson on the kitchen door: "
        f'"{world.facts["lesson"]}"'
    )
    world.facts["resolved"] = True
    return world


def valid_recipes() -> list[str]:
    return sorted(RECIPES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    recipe = args.recipe or rng.choice(valid_recipes())
    if recipe not in RECIPES:
        raise StoryError(f"Unknown recipe: {recipe}")
    return StoryParams(
        recipe=recipe,
        name=args.name or rng.choice(NAMES),
        role=args.role or rng.choice(ROLES),
        opening=rng.randrange(len(OPENINGS)),
        lesson=rng.randrange(len(LESSONS)),
    )


def generation_prompts(world: World) -> list[str]:
    recipe: Recipe = world.facts["recipe"]
    return [
        f"Write an Animal Story about a chef making {recipe.dish}.",
        f"Tell a cautionary animal story in which a chef takes {recipe.ingredient} without asking.",
        "Write a story with a bad ending, a morbid mistake, dialogue, and a later repair attempt.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    recipe: Recipe = f["recipe"]
    chef: Entity = f["chef"]
    animal: Entity = f["animal"]
    return [
        QAItem(
            question=f"What was Chef {chef.id} trying to make?",
            answer=f"Chef {chef.id} was trying to make {recipe.dish} with {recipe.ingredient}.",
        ),
        QAItem(
            question=f"Why did the {animal.label} object?",
            answer=f"The {animal.label} objected because {recipe.clue.lower()} Chef {chef.id} took food that belonged to the animal without asking.",
        ),
        QAItem(
            question="What made the ending bad?",
            answer=f"The mistake spoiled the plan: {recipe.consequence} The first dish could not be saved.",
        ),
        QAItem(
            question=f"What did the {animal.label} say?",
            answer=f'The {animal.label} said, {recipe.dialogue}',
        ),
        QAItem(
            question="How did the chef try to repair the mistake?",
            answer=recipe.repair,
        ),
        QAItem(
            question="What lesson did the chef learn?",
            answer=f'The chef learned: "{f["lesson"]}"',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a chef do?",
            answer="A chef prepares food, follows recipes, and helps keep a kitchen safe and organized.",
        ),
        QAItem(
            question="Why should someone ask before taking food?",
            answer="Asking shows respect and helps a person learn whether the food belongs to someone else or is needed for another purpose.",
        ),
        QAItem(
            question="What does morbid mean?",
            answer="Morbid can describe something grim, gloomy, or concerned with death. In this story, the word describes the chef's gloomy mistake, not harm to the animal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
chef(C) :- chef_entity(C).
animal(A) :- animal_entity(A).
bad_ending(R) :- recipe(R), spoiled(R), regret(R).
repair(R) :- recipe(R), apology(R), safer_plan(R).
valid_story(R) :- recipe(R), bad_ending(R), repair(R).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for recipe_id, recipe in RECIPES.items():
        lines.append(asp.fact("recipe", recipe_id))
        lines.append(asp.fact("animal_entity", recipe.animal))
        lines.append(asp.fact("dish", recipe_id, recipe.dish))
        lines.append(asp.fact("spoiled", recipe_id))
        lines.append(asp.fact("regret", recipe_id))
        lines.append(asp.fact("apology", recipe_id))
        lines.append(asp.fact("safer_plan", recipe_id))
    lines.append(asp.fact("chef_entity", "chef"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_recipes() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted({row[0] for row in asp.atoms(model, "valid_story")})


def asp_verify() -> int:
    py = set(valid_recipes())
    clingo_recipes = set(asp_valid_recipes())
    if py == clingo_recipes:
        print(f"OK: clingo gate matches valid_recipes() ({len(py)} recipes).")
        for recipe_id in valid_recipes():
            sample = generate(
                StoryParams(recipe_id, "Basil", "young chef", 0, 0)
            )
            if not sample.story or "bad" not in sample.story.lower():
                print(f"Generated story check failed for {recipe_id}.")
                return 1
        print("OK: generated stories exercised.")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in python:", sorted(py - clingo_recipes))
    print("  only in clingo:", sorted(clingo_recipes - py))
    return 1


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal Story chef world with a bad ending."
    )
    parser.add_argument("--recipe", choices=sorted(RECIPES))
    parser.add_argument("--name")
    parser.add_argument("--role", choices=ROLES)
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


CURATED = [
    StoryParams("berry_pie", "Basil", "young chef", 0, 0),
    StoryParams("carrot_soup", "Mara", "apprentice chef", 1, 1),
    StoryParams("honey_biscuits", "Pip", "careful chef", 2, 2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(item) for item in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            attempt += 1
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
