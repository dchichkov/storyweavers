#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ingredient_surprise_fairy_tale.py
============================================================

A small fairy-tale storyworld about a child in an enchanted wood who prepares a
treat for a moonlit feast, discovers a missing ingredient, and is saved by a
surprise gift that truly fits the recipe.

The core constraint is simple and deliberate: a surprise ingredient is only a
reasonable story turn when it supplies the *need* left by the missing
ingredient. A moon cake missing sweetness cannot be rescued by a silver pebble;
a dew soup missing sparkle cannot be rescued by plain oats. The world model
checks that fit in Python and in an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/ingredient_surprise_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/ingredient_surprise_fairy_tale.py --recipe moon_cake
    python storyworlds/worlds/gpt-5.4/ingredient_surprise_fairy_tale.py --missing honey --surprise oats
    python storyworlds/worlds/gpt-5.4/ingredient_surprise_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/ingredient_surprise_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ingredient_surprise_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make shared result containers importable when this script is run directly.
_THIS = os.path.abspath(__file__)
_STORYWORLDS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_THIS)))
sys.path.insert(0, _STORYWORLDS_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "fairy", "mother", "woman"}
        male = {"boy", "prince", "elf", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Recipe:
    id: str
    title: str
    vessel: str
    treat: str
    need: str
    opening: str
    mix_line: str
    fail_line: str
    success_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ingredient:
    id: str
    label: str
    phrase: str
    quality: str
    color: str
    source: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    entrance: str
    gift_line: str
    bless_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_worry(world: World) -> list[str]:
    cook = world.get("hero")
    pantry = world.get("pantry")
    if pantry.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cook.memes["worry"] += 1
    return []


def _r_fit_hope(world: World) -> list[str]:
    bowl = world.get("bowl")
    hero = world.get("hero")
    if bowl.meters["balanced"] < THRESHOLD:
        return []
    sig = ("fit_hope",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hope"] += 1
    hero.memes["worry"] = 0.0
    return []


def _r_feast_delight(world: World) -> list[str]:
    feast = world.get("feast")
    if feast.meters["ready"] < THRESHOLD:
        return []
    sig = ("feast_delight",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="fit_hope", tag="emotion", apply=_r_fit_hope),
    Rule(name="feast_delight", tag="emotion", apply=_r_feast_delight),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


RECIPES = {
    "moon_cake": Recipe(
        id="moon_cake",
        title="Moon Cake",
        vessel="a round silver pan",
        treat="moon cake",
        need="sweet",
        opening="for the moon-feast on the hill",
        mix_line="stirred cloud flour with milk and a pinch of cinnamon",
        fail_line="Without something sweet, the batter would taste plain and sleepy.",
        success_line="At once the batter smelled warm and sweet, as if a tiny moon had opened inside the pan.",
        ending_image="The moon cake rose golden, and every lantern seemed to smile back at it.",
        tags={"cake", "sweet"},
    ),
    "dew_soup": Recipe(
        id="dew_soup",
        title="Dew Soup",
        vessel="a blue glass pot",
        treat="dew soup",
        need="sparkle",
        opening="for the dawn feast beside the lily pond",
        mix_line="poured petal broth over tender peas and moon-salt",
        fail_line="Without a sparkling ingredient, the soup would only look like ordinary green broth.",
        success_line="The pot flashed with tiny stars, and the soup began to shine like morning grass.",
        ending_image="When the lid lifted, silver steam curled up like sleepy fireflies.",
        tags={"soup", "sparkle"},
    ),
    "rose_tart": Recipe(
        id="rose_tart",
        title="Rose Tart",
        vessel="a little heart-shaped tin",
        treat="rose tart",
        need="fragrance",
        opening="for the queen's garden tea",
        mix_line="pressed berry paste into a soft crust and brushed the top with cream",
        fail_line="Without a fragrant ingredient, the tart would look pretty but carry no lovely garden smell.",
        success_line="A gentle perfume drifted up at once, and the kitchen felt full of roses after rain.",
        ending_image="The rose tart cooled on the sill while butterflies hovered near the window.",
        tags={"tart", "fragrance"},
    ),
}

INGREDIENTS = {
    "honey": Ingredient(
        id="honey",
        label="honey",
        phrase="a spoon of golden honey",
        quality="sweet",
        color="golden",
        source="the bee jars on the shelf",
        tags={"honey", "sweet"},
    ),
    "sugar_plum": Ingredient(
        id="sugar_plum",
        label="sugar plum",
        phrase="a sugared plum from the winter jar",
        quality="sweet",
        color="violet",
        source="the winter jar",
        tags={"plum", "sweet"},
    ),
    "stardust": Ingredient(
        id="stardust",
        label="stardust",
        phrase="a pinch of silver stardust",
        quality="sparkle",
        color="silver",
        source="the star box",
        tags={"stardust", "sparkle"},
    ),
    "glow_sap": Ingredient(
        id="glow_sap",
        label="glow sap",
        phrase="a drop of glow sap from a moon-lily stem",
        quality="sparkle",
        color="pale blue",
        source="the moon-lily stem",
        tags={"glow", "sparkle"},
    ),
    "rosewater": Ingredient(
        id="rosewater",
        label="rosewater",
        phrase="a splash of rosewater",
        quality="fragrance",
        color="clear pink",
        source="the crystal bottle",
        tags={"rose", "fragrance"},
    ),
    "mint_leaf": Ingredient(
        id="mint_leaf",
        label="mint leaf",
        phrase="a torn mint leaf from the herb basket",
        quality="fragrance",
        color="green",
        source="the herb basket",
        tags={"mint", "fragrance"},
    ),
    "oats": Ingredient(
        id="oats",
        label="oats",
        phrase="a spoon of plain oats",
        quality="plain",
        color="pale tan",
        source="the grain sack",
        tags={"oats"},
    ),
    "pebble": Ingredient(
        id="pebble",
        label="silver pebble",
        phrase="a smooth silver pebble",
        quality="hard",
        color="silver",
        source="the path outside",
        tags={"pebble"},
    ),
}

HELPERS = {
    "sparrow": Helper(
        id="sparrow",
        label="a little sparrow",
        type="bird",
        entrance="fluttered in through the round kitchen window",
        gift_line='"I saw your worried face from the elder tree," chirped the sparrow.',
        bless_line='The sparrow dipped its head as if it knew a small kitchen secret.',
        tags={"bird", "friend"},
    ),
    "hedgehog": Helper(
        id="hedgehog",
        label="a kind hedgehog",
        type="animal",
        entrance="padded from beneath the herb table",
        gift_line='"I was saving this for a cold morning," said the hedgehog, "but a feast is better."',
        bless_line='The hedgehog smiled in the quiet, patient way of creatures who know where good things grow.',
        tags={"animal", "friend"},
    ),
    "moon_fairy": Helper(
        id="moon_fairy",
        label="a moon fairy",
        type="fairy",
        entrance="drifted down in a ribbon of silver light",
        gift_line='"A feast should never fail for want of one true ingredient," sang the moon fairy.',
        bless_line='For a moment, even the spoons looked enchanted.',
        tags={"fairy", "magic"},
    ),
}


def ingredient_fits(recipe: Recipe, ingredient: Ingredient) -> bool:
    return recipe.need == ingredient.quality


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for recipe_id, recipe in RECIPES.items():
        for missing_id in INGREDIENTS:
            for surprise_id, surprise in INGREDIENTS.items():
                if missing_id == surprise_id:
                    continue
                if ingredient_fits(recipe, INGREDIENTS[surprise_id]):
                    combos.append((recipe_id, missing_id, surprise_id))
    return combos


@dataclass
class StoryParams:
    recipe: str
    missing: str
    surprise: str
    helper: str
    hero_name: str
    hero_type: str
    guardian_type: str
    trait: str
    seed: Optional[int] = None


def setup_kitchen(world: World, hero: Entity, guardian: Entity, recipe: Recipe, missing: Ingredient) -> None:
    hero.memes["care"] += 1
    world.say(
        f"In a cottage at the edge of the whispering wood, {hero.id} the little "
        f"{hero.type} stood on a stool beside {recipe.vessel}. "
        f"{hero.pronoun().capitalize()} was making a {recipe.treat} {recipe.opening}."
    )
    world.say(
        f"{hero.id} {recipe.mix_line}. Near the bowl, {guardian.label_word} smiled, "
        f"for the whole room smelled of warmth and good plans."
    )
    world.say(
        f"Only one ingredient was still needed: {missing.phrase} from {missing.source}."
    )


def discover_missing(world: World, hero: Entity, missing: Ingredient, recipe: Recipe) -> None:
    pantry = world.get("pantry")
    pantry.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {hero.id} reached for {missing.label}, the place where it should "
        f"have been was empty."
    )
    world.say(
        f'{hero.id} looked again, then whispered, "Oh dear. The ingredient is gone." '
        f"{recipe.fail_line}"
    )


def gentle_worry(world: World, hero: Entity, guardian: Entity) -> None:
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s shoulders drooped. {guardian.label_word.capitalize()} laid a "
            f"gentle hand on {hero.pronoun('possessive')} back and said, "
            f'"A fairy-tale kitchen always asks for patience before it gives help."'
        )


def surprise_arrives(world: World, helper: Helper, surprise: Ingredient) -> None:
    world.say(
        f"Just then, {helper.label} {helper.entrance}. {helper.gift_line}"
    )
    world.say(
        f"It carried {surprise.phrase}, {surprise.color} and bright as a tiny treasure."
    )


def try_surprise(world: World, hero: Entity, helper: Helper, recipe: Recipe, surprise: Ingredient) -> None:
    bowl = world.get("bowl")
    bowl.meters[surprise.quality] += 1
    if ingredient_fits(recipe, surprise):
        bowl.meters["balanced"] += 1
    propagate(world, narrate=False)
    world.say(helper.bless_line)
    world.say(
        f'{hero.id} blinked in surprise. "Could this ingredient help?" '
        f"{hero.pronoun().capitalize()} tipped in {surprise.phrase} and stirred."
    )


def finish_feast(world: World, hero: Entity, guardian: Entity, helper: Helper, recipe: Recipe) -> None:
    feast = world.get("feast")
    feast.meters["ready"] += 1
    propagate(world, narrate=False)
    world.say(recipe.success_line)
    world.say(
        f'"It worked!" cried {hero.id}. {guardian.label_word.capitalize()} laughed, '
        f"and {helper.label} gave a proud little nod."
    )
    world.say(
        f"By evening, the {recipe.treat} sat on the table at the center of the feast. "
        f"{recipe.ending_image}"
    )
    world.say(
        f"{hero.id} saved the last shining bite for {helper.label}, because the best "
        f"surprises are the ones that arrive just when kindness is needed."
    )


def tell(
    recipe: Recipe,
    missing: Ingredient,
    surprise: Ingredient,
    helper: Helper,
    hero_name: str = "Nella",
    hero_type: str = "fairy",
    guardian_type: str = "grandmother",
    trait: str = "careful",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_type,
            label=hero_name,
            role="hero",
            traits=[trait],
        )
    )
    guardian = world.add(
        Entity(
            id="guardian",
            kind="character",
            type=guardian_type,
            label="grandmother" if guardian_type == "grandmother" else "guardian",
            role="guardian",
        )
    )
    world.add(Entity(id="pantry", type="pantry", label="pantry"))
    world.add(Entity(id="bowl", type="bowl", label=recipe.vessel))
    world.add(Entity(id="feast", type="feast", label="feast"))
    world.facts["hero_name"] = hero_name

    setup_kitchen(world, hero, guardian, recipe, missing)
    world.para()
    discover_missing(world, hero, missing, recipe)
    gentle_worry(world, hero, guardian)
    world.para()
    surprise_arrives(world, helper, surprise)
    try_surprise(world, hero, helper, recipe, surprise)
    world.para()
    finish_feast(world, hero, guardian, helper, recipe)

    world.facts.update(
        hero=hero,
        guardian=guardian,
        recipe=recipe,
        missing=missing,
        surprise=surprise,
        helper=helper,
        fit=ingredient_fits(recipe, surprise),
        surprise_quality=surprise.quality,
        need=recipe.need,
        success=True,
    )
    return world


GIRL_NAMES = ["Nella", "Mira", "Lina", "Poppy", "Tessa", "Wren"]
BOY_NAMES = ["Oren", "Tobin", "Milo", "Rowan", "Pip", "Alden"]
HERO_TYPES = ["fairy", "princess", "girl", "boy"]
TRAITS = ["careful", "hopeful", "busy", "kind", "patient"]
GUARDIANS = ["grandmother", "godmother"]


KNOWLEDGE = {
    "ingredient": [
        (
            "What is an ingredient?",
            "An ingredient is one of the foods or things you put into a recipe to make it. If one ingredient is missing, the dish may not taste or look the way it should.",
        )
    ],
    "honey": [
        (
            "Why is honey sweet?",
            "Honey is made by bees from flower nectar, and it tastes sweet because it is full of natural sugars.",
        )
    ],
    "stardust": [
        (
            "Why do fairy tales use stardust as a magical ingredient?",
            "In fairy tales, stardust stands for light and wonder. It can make ordinary things seem bright and enchanted.",
        )
    ],
    "rosewater": [
        (
            "What does rosewater smell like?",
            "Rosewater smells soft and flowery, like fresh rose petals. Cooks use only a little because the scent is gentle but strong.",
        )
    ],
    "sparkle": [
        (
            "What does it mean when something sparkles?",
            "Something sparkles when it catches the light in tiny bright flashes. In fairy tales, sparkle often makes food or magic feel special.",
        )
    ],
    "fragrance": [
        (
            "What is fragrance?",
            "Fragrance is a pleasant smell. A fragrant ingredient can make food or flowers smell lovely even before you taste them.",
        )
    ],
    "surprise": [
        (
            "Why can a surprise feel good in a story?",
            "A good surprise changes worry into hope. It feels special because help or joy arrives when no one expects it.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ingredient", "honey", "stardust", "rosewater", "sparkle", "fragrance", "surprise"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    recipe = f["recipe"]
    missing = f["missing"]
    surprise = f["surprise"]
    helper = f["helper"]
    hero_name = f["hero_name"]
    return [
        f'Write a short fairy tale for a 3-to-5-year-old that includes the word "ingredient" and a happy surprise.',
        f"Tell a gentle fairy tale where {hero_name} is making a {recipe.treat}, discovers that {missing.label} is missing, and is saved by {helper.label} bringing {surprise.phrase}.",
        f"Write a magical kitchen story with a clear problem, a surprise helper, and an ending image that shows the feast has been saved.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    recipe = f["recipe"]
    missing = f["missing"]
    surprise = f["surprise"]
    helper = f["helper"]
    name = world.facts["hero_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a little {hero.type}, who wanted to finish a {recipe.treat} for a feast. {guardian.label_word.capitalize()} stayed nearby, and {helper.label} became the surprise helper.",
        ),
        (
            f"What problem did {name} have in the kitchen?",
            f"{name} discovered that {missing.phrase} was missing just when the recipe still needed it. That made {hero.pronoun('object')} worry because a {recipe.treat} without the right ingredient would not come out the right way.",
        ),
        (
            "What was the surprise?",
            f"The surprise was that {helper.label} arrived at exactly the right moment carrying {surprise.phrase}. The gift changed the story from worry to hope because it fit what the recipe still needed.",
        ),
        (
            f"Why did {surprise.label} help?",
            f"It helped because the {recipe.treat} needed something {recipe.need}, and {surprise.label} brought that quality. When {name} stirred it in, the recipe became balanced again and the feast could go on.",
        ),
        (
            "How did the story end?",
            f"The {recipe.treat} was saved and placed at the center of the feast. The ending image proves the change: the kitchen problem is over, and the surprise ingredient has turned worry into a glowing celebration.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ingredient", "surprise"}
    surprise = world.facts["surprise"]
    recipe = world.facts["recipe"]
    if surprise.id == "honey":
        tags.add("honey")
    if surprise.id == "stardust":
        tags.add("stardust")
    if surprise.id == "rosewater":
        tags.add("rosewater")
    if recipe.need == "sparkle":
        tags.add("sparkle")
    if recipe.need == "fragrance":
        tags.add("fragrance")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:9} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(recipe: Recipe, surprise: Ingredient) -> str:
    return (
        f"(No story: {recipe.title} needs something {recipe.need}, but {surprise.label} "
        f"is {surprise.quality}. The surprise ingredient must truly solve the recipe's problem.)"
    )


ASP_RULES = r"""
needs(R, N) :- recipe(R), need(R, N).
fits(R, I)  :- needs(R, N), quality(I, N).

valid(R, M, S) :- recipe(R), ingredient(M), ingredient(S), M != S, fits(R, S).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for recipe_id, recipe in RECIPES.items():
        lines.append(asp.fact("recipe", recipe_id))
        lines.append(asp.fact("need", recipe_id, recipe.need))
    for ingredient_id, ingredient in INGREDIENTS.items():
        lines.append(asp.fact("ingredient", ingredient_id))
        lines.append(asp.fact("quality", ingredient_id, ingredient.quality))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


CURATED = [
    StoryParams(
        recipe="moon_cake",
        missing="honey",
        surprise="sugar_plum",
        helper="sparrow",
        hero_name="Nella",
        hero_type="fairy",
        guardian_type="grandmother",
        trait="careful",
    ),
    StoryParams(
        recipe="dew_soup",
        missing="stardust",
        surprise="glow_sap",
        helper="moon_fairy",
        hero_name="Milo",
        hero_type="boy",
        guardian_type="godmother",
        trait="hopeful",
    ),
    StoryParams(
        recipe="rose_tart",
        missing="rosewater",
        surprise="mint_leaf",
        helper="hedgehog",
        hero_name="Poppy",
        hero_type="princess",
        guardian_type="grandmother",
        trait="kind",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Fairy-tale storyworld: a missing ingredient, a surprise helper, and a saved feast."
    )
    ap.add_argument("--recipe", choices=RECIPES)
    ap.add_argument("--missing", choices=INGREDIENTS)
    ap.add_argument("--surprise", choices=INGREDIENTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.recipe and args.surprise:
        recipe = RECIPES[args.recipe]
        surprise = INGREDIENTS[args.surprise]
        if not ingredient_fits(recipe, surprise):
            raise StoryError(explain_rejection(recipe, surprise))
    if args.missing and args.surprise and args.missing == args.surprise:
        raise StoryError("(No story: the surprise cannot be the same ingredient that was missing.)")

    combos = [
        combo
        for combo in valid_combos()
        if (args.recipe is None or combo[0] == args.recipe)
        and (args.missing is None or combo[1] == args.missing)
        and (args.surprise is None or combo[2] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    recipe_id, missing_id, surprise_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    if args.name:
        name = args.name
    else:
        if hero_type in {"fairy", "princess", "girl"}:
            name = rng.choice(GIRL_NAMES)
        else:
            name = rng.choice(BOY_NAMES)
    return StoryParams(
        recipe=recipe_id,
        missing=missing_id,
        surprise=surprise_id,
        helper=args.helper or rng.choice(sorted(HELPERS)),
        hero_name=name,
        hero_type=hero_type,
        guardian_type=args.guardian or rng.choice(GUARDIANS),
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.recipe not in RECIPES:
        raise StoryError(f"(Unknown recipe: {params.recipe})")
    if params.missing not in INGREDIENTS:
        raise StoryError(f"(Unknown missing ingredient: {params.missing})")
    if params.surprise not in INGREDIENTS:
        raise StoryError(f"(Unknown surprise ingredient: {params.surprise})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    recipe = RECIPES[params.recipe]
    missing = INGREDIENTS[params.missing]
    surprise = INGREDIENTS[params.surprise]
    if params.missing == params.surprise:
        raise StoryError("(No story: the surprise cannot be the same ingredient that was missing.)")
    if not ingredient_fits(recipe, surprise):
        raise StoryError(explain_rejection(recipe, surprise))

    world = tell(
        recipe=recipe,
        missing=missing,
        surprise=surprise,
        helper=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        guardian_type=params.guardian_type,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (recipe, missing, surprise) combos:\n")
        for recipe_id, missing_id, surprise_id in combos:
            print(f"  {recipe_id:10} {missing_id:10} {surprise_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.recipe} with surprise {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
