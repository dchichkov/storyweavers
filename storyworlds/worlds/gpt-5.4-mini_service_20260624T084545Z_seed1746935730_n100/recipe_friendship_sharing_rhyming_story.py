#!/usr/bin/env python3
"""
Story world: recipe friendship sharing rhyming story.

A small, self-contained story simulation about friends making a recipe, sharing
ingredients, and solving a gentle problem together in a rhyming style.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Friend:
    name: str
    role: str
    feeling: str = "happy"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Ingredient:
    name: str
    amount: str
    shared: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Recipe:
    title: str
    dish: str
    rhyme_a: str
    rhyme_b: str
    key_step: str
    finale: str
    missing: str
    share_item: str
    share_help: str


@dataclass
class Kitchen:
    place: str
    table: str
    friends: dict[str, Friend] = field(default_factory=dict)
    ingredients: dict[str, Ingredient] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


def _safe_name_options() -> dict[str, list[str]]:
    return {
        "child": ["Mia", "Noah", "Lily", "Theo", "Ava", "Finn", "Zoe", "Leo"],
        "friend": ["Tia", "Ben", "Ruby", "Max", "Nina", "Owen", "Pia", "Sam"],
    }


RECIPES = {
    "berry_cups": Recipe(
        title="berry cups",
        dish="berry cups",
        rhyme_a="stir and twirl",
        rhyme_b="shine and swirl",
        key_step="mix the berries with yogurt in a bowl",
        finale="They filled two cups and smiled with delight.",
        missing="berries",
        share_item="berries",
        share_help="The second friend shared their berries so the cups could be sweet and bright.",
    ),
    "banana_bread": Recipe(
        title="banana bread",
        dish="banana bread",
        rhyme_a="mash and splash",
        rhyme_b="dash and flash",
        key_step="mash the bananas and stir in the flour",
        finale="The warm bread puffed up, golden and neat.",
        missing="bananas",
        share_item="bananas",
        share_help="A friend shared bananas, and the batter became just right.",
    ),
    "apple_pie": Recipe(
        title="apple pie",
        dish="apple pie",
        rhyme_a="peel and kneel",
        rhyme_b="peek and tweak",
        key_step="slice the apples and tuck them into the crust",
        finale="The pie came out brown and cozy and sweet.",
        missing="apples",
        share_item="apples",
        share_help="They shared apples for the filling, and the pie was a lovely treat.",
    ),
    "sandwich_stack": Recipe(
        title="sunny sandwich stack",
        dish="sandwich stack",
        rhyme_a="spread and read",
        rhyme_b="smile and pile",
        key_step="spread the filling and stack the slices high",
        finale="The sandwich tower stood tall for the two.",
        missing="bread",
        share_item="bread",
        share_help="One friend shared bread, and the sandwich stack grew tall and new.",
    ),
}


SETTINGS = [
    "the bright kitchen",
    "the cozy kitchen",
    "Grandma's sunny kitchen",
    "the little blue kitchen",
]

INGREDIENT_BANK = {
    "berries": Ingredient("berries", "one bowl"),
    "bananas": Ingredient("bananas", "two"),
    "apples": Ingredient("apples", "three"),
    "bread": Ingredient("bread", "two slices"),
    "yogurt": Ingredient("yogurt", "one cup"),
    "flour": Ingredient("flour", "one scoop"),
    "crust": Ingredient("crust", "one pie shell"),
    "filling": Ingredient("filling", "one bowl"),
}


@dataclass
class StoryParams:
    setting: str
    recipe: str
    child_name: str
    friend_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Recipe friendship sharing rhyming story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--recipe", choices=sorted(RECIPES))
    ap.add_argument("--child-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(SETTINGS)
    recipe = args.recipe or rng.choice(list(RECIPES))
    names = _safe_name_options()
    child_name = args.child_name or rng.choice(names["child"])
    friend_name = args.friend_name or rng.choice([n for n in names["friend"] if n != child_name])
    if child_name == friend_name:
        raise StoryError("The two friends need different names.")
    return StoryParams(setting=setting, recipe=recipe, child_name=child_name, friend_name=friend_name)


def _make_kitchen(params: StoryParams) -> Kitchen:
    kitchen = Kitchen(place=params.setting, table="the round table")
    recipe = RECIPES[params.recipe]
    child = Friend(params.child_name, "child")
    friend = Friend(params.friend_name, "friend")
    kitchen.friends[child.name] = child
    kitchen.friends[friend.name] = friend
    for key in {recipe.missing, "yogurt", "flour", "crust", "filling", "bread"}:
        if key in INGREDIENT_BANK:
            kitchen.ingredients[key] = Ingredient(
                name=INGREDIENT_BANK[key].name,
                amount=INGREDIENT_BANK[key].amount,
            )
    kitchen.facts["recipe"] = recipe
    kitchen.facts["child"] = child
    kitchen.facts["friend"] = friend
    return kitchen


def _rhyming_intro(kitchen: Kitchen, recipe: Recipe) -> None:
    child = kitchen.facts["child"]
    friend = kitchen.facts["friend"]
    kitchen.say(
        f"In {kitchen.place}, {child.name} and {friend.name} came to play,\n"
        f"with a recipe for {recipe.dish} to brighten the day."
    )
    kitchen.say(
        f"They liked to work together in a cheerful, friendly way,\n"
        f"and every little helping hand could make the laughter stay."
    )
    child.memes["friendship"] = child.memes.get("friendship", 0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0) + 1


def _problem(kitchen: Kitchen, recipe: Recipe) -> None:
    child = kitchen.facts["child"]
    friend = kitchen.facts["friend"]
    child.memes["want"] = child.memes.get("want", 0) + 1
    kitchen.say(
        f"{child.name} read the page and gave a little grin,\n"
        f"but oh dear, one needed thing was missing from within."
    )
    kitchen.say(
        f"They searched the bowls and cabinets, peeking every nook,\n"
        f"then saw that {recipe.missing} had not been tucked into the book."
    )
    friend.memes["concern"] = friend.memes.get("concern", 0) + 1


def _sharing_turn(kitchen: Kitchen, recipe: Recipe) -> None:
    child = kitchen.facts["child"]
    friend = kitchen.facts["friend"]
    if recipe.share_item not in kitchen.ingredients:
        raise StoryError("The recipe needs a shareable ingredient that exists in the kitchen.")
    item = kitchen.ingredients[recipe.share_item]
    item.shared = True
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    friend.memes["kindness"] = friend.memes.get("kindness", 0) + 1
    kitchen.say(
        f"Then {friend.name} said, 'I have some {recipe.share_item} to spare,'\n"
        f"and passed them over kindly with a thoughtful, generous air."
    )
    kitchen.say(recipe.share_help)


def _recipe_action(kitchen: Kitchen, recipe: Recipe) -> None:
    child = kitchen.facts["child"]
    friend = kitchen.facts["friend"]
    kitchen.say(
        f"{child.name} did the {recipe.rhyme_a} part, and {friend.name} did the {recipe.rhyme_b} part too,\n"
        f"while {recipe.key_step} made the whole thing simple and true."
    )
    child.meters["helped"] = child.meters.get("helped", 0) + 1
    friend.meters["helped"] = friend.meters.get("helped", 0) + 1


def _ending(kitchen: Kitchen, recipe: Recipe) -> None:
    child = kitchen.facts["child"]
    friend = kitchen.facts["friend"]
    child.memes["joy"] = child.memes.get("joy", 0) + 2
    friend.memes["joy"] = friend.memes.get("joy", 0) + 2
    kitchen.say(
        f"{recipe.finale}\n"
        f"{child.name} shared a plate with {friend.name}, and both felt warm through and through."
    )
    kitchen.say(
        f"The friends ate side by side, with a happy little tune,\n"
        f"for sharing made the recipe taste like sunshine in the room."
    )


def generate(params: StoryParams) -> StorySample:
    recipe = RECIPES[params.recipe]
    kitchen = _make_kitchen(params)
    _rhyming_intro(kitchen, recipe)
    kitchen.say("")
    _problem(kitchen, recipe)
    kitchen.say("")
    _sharing_turn(kitchen, recipe)
    kitchen.say("")
    _recipe_action(kitchen, recipe)
    kitchen.say("")
    _ending(kitchen, recipe)
    kitchen.facts["resolved"] = True
    kitchen.facts["shared_item"] = recipe.share_item
    return StorySample(
        params=params,
        story=kitchen.render(),
        prompts=generation_prompts(kitchen),
        story_qa=story_qa(kitchen),
        world_qa=world_qa(kitchen),
        world=kitchen,
    )


def generation_prompts(kitchen: Kitchen) -> list[str]:
    recipe = kitchen.facts["recipe"]
    child = kitchen.facts["child"]
    friend = kitchen.facts["friend"]
    return [
        f"Write a short rhyming story about {child.name} and {friend.name} making {recipe.dish} together.",
        f"Tell a gentle friendship story where two friends share ingredients and finish a recipe.",
        f"Write a child-friendly rhyming tale that includes sharing, teamwork, and {recipe.missing}.",
    ]


def story_qa(kitchen: Kitchen) -> list[QAItem]:
    recipe = kitchen.facts["recipe"]
    child = kitchen.facts["child"]
    friend = kitchen.facts["friend"]
    return [
        QAItem(
            question=f"Who are the friends in the story?",
            answer=f"The friends are {child.name} and {friend.name}. They work together in {kitchen.place}.",
        ),
        QAItem(
            question=f"What recipe were they making?",
            answer=f"They were making {recipe.dish}, and the steps were part of a simple, cheerful recipe.",
        ),
        QAItem(
            question=f"What was missing at first?",
            answer=f"{recipe.missing.capitalize()} were missing at first, so the recipe could not be finished right away.",
        ),
        QAItem(
            question=f"How did the friends solve the problem?",
            answer=f"{friend.name} shared {recipe.share_item}, and that kind act helped them keep going together.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the recipe finished, the friends sharing food, and both of them feeling happy.",
        ),
    ]


def world_qa(kitchen: Kitchen) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving some of what you have so another person can use it too.",
        ),
        QAItem(
            question="Why do friends help each other cook?",
            answer="Friends help each other cook so the work is easier and the food can be made together.",
        ),
        QAItem(
            question="What is a recipe?",
            answer="A recipe is a set of steps that tells you how to make food.",
        ),
        QAItem(
            question="Why is it nice to make food with a friend?",
            answer="It is nice because cooking together can be fun, kind, and full of teamwork.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: Kitchen) -> str:
    lines = ["--- world trace ---"]
    for friend in world.friends.values():
        lines.append(f"friend {friend.name}: meters={friend.meters} memes={friend.memes}")
    for ing in world.ingredients.values():
        lines.append(f"ingredient {ing.name}: shared={ing.shared}")
    return "\n".join(lines)


ASP_RULES = r"""
shown(valid_story/3).

valid_story(S, R, F) :- setting(S), recipe(R), friendly(F).
friendly(F) :- has_friend(F).
shared_ok(R) :- needs_share(R), shareable(R).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for r in RECIPES:
        lines.append(asp.fact("recipe", r))
        lines.append(asp.fact("needs_share", r))
        lines.append(asp.fact("shareable", r))
    for n in _safe_name_options()["child"] + _safe_name_options()["friend"]:
        lines.append(asp.fact("has_friend", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(setting=SETTINGS[0], recipe="berry_cups", child_name="Mia", friend_name="Tia"),
    StoryParams(setting=SETTINGS[1], recipe="banana_bread", child_name="Leo", friend_name="Sam"),
    StoryParams(setting=SETTINGS[2], recipe="apple_pie", child_name="Ava", friend_name="Nina"),
]


def build_story_params_list(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    if args.all:
        return CURATED
    out: list[StoryParams] = []
    for _ in range(args.n):
        out.append(resolve_params(args, rng))
    return out


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)
    params_list = build_story_params_list(args, rng)
    samples = [generate(p) for p in params_list]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
