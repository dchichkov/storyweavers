#!/usr/bin/env python3
"""
A small comedy storyworld about lard, suspense, friendship, and transformation.

Seed tale sketch:
A child and a friend find a jar of lard in a kitchen. They think it is something
mysterious, but it turns out to be useful for making pie crust. While they wait
for the crust, they worry, help each other, and end up with a funny surprise:
the plain blob of lard becomes a flaky pastry, and their friendship becomes
stronger too.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    state: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Ingredient:
    id: str
    label: str
    phrase: str
    mess: str
    suspenseful: bool = False
    transform_into: str = ""


@dataclass
class Helper:
    id: str
    label: str
    prep: str
    reveal: str
    result: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"peek", "cook", "wait"}),
    "bakery": Setting(place="the bakery", affords={"peek", "cook", "wait"}),
}

INGREDIENTS = {
    "lard": Ingredient(
        id="lard",
        label="lard",
        phrase="a small jar of lard",
        mess="greasy",
        suspenseful=True,
        transform_into="pie crust",
    ),
    "butter": Ingredient(
        id="butter",
        label="butter",
        phrase="a yellow stick of butter",
        mess="soft",
        suspenseful=False,
        transform_into="cookie dough",
    ),
}

HELPERS = {
    "grandma": Helper(
        id="grandma",
        label="Grandma",
        prep="showed them how to mix it",
        reveal="smiled and said the jar was for baking",
        result="the dough puffed up into a flaky pie crust",
    ),
    "friend": Helper(
        id="friend",
        label="a friend",
        prep="laughed and helped them stir",
        reveal="pointed at the recipe card",
        result="the mixture turned into a silly, shiny crust",
    ),
}

HEROES = [
    ("Maya", "girl"),
    ("Noah", "boy"),
    ("Lina", "girl"),
    ("Theo", "boy"),
]

TRAITS = ["curious", "cheerful", "brave", "silly"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    ingredient: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when a place affords the action, the ingredient creates
% suspense, and a helper can reveal the joke and support the transformation.
valid_story(P, I, H) :- affords(P, cook), ingredient(I), suspenseful(I),
                        helper(H), can_reveal(H), can_transform(I).

% Friendship is part of the tale if a helper is present.
friendship_story(H) :- helper(H).

% A transformation story exists if the ingredient has a result.
transformation_story(I) :- ingredient(I), can_transform(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for act in sorted(s.affords):
            lines.append(asp.fact("affords", pid, act))
    for iid, ing in INGREDIENTS.items():
        lines.append(asp.fact("ingredient", iid))
        if ing.suspenseful:
            lines.append(asp.fact("suspenseful", iid))
        if ing.transform_into:
            lines.append(asp.fact("can_transform", iid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("can_reveal", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3.\n#show friendship_story/1.\n#show transformation_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for ingredient in INGREDIENTS:
            for helper in HELPERS:
                if ingredient == "lard":
                    combos.append((place, ingredient, helper))
    return combos


def explain_rejection(ingredient: Ingredient) -> str:
    return f"(No story: this world only supports a funny suspense-and-transformation tale around {ingredient.label}.)"


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def predict_transformation(world: World, ingredient: Entity) -> bool:
    sim = world.copy()
    ing = sim.get(ingredient.id)
    ing.meters["warmth"] = ing.meters.get("warmth", 0) + 1
    ing.state = "melting"
    return ingredient.id == "lard"


def intro(world: World, hero: Entity, helper: Entity, ing: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.pronoun('possessive')} {hero.memes.get('trait', 'curious')} little {hero.type} who loved baking."
    )
    world.say(
        f"One day, {hero.id} and {helper.label.lower()} found {ing.phrase} on the counter."
    )


def suspense(world: World, hero: Entity, helper: Entity, ing: Entity) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0) + 1
    world.say(
        f"They stared at the jar. It looked mysterious, and {hero.id} whispered, "
        f'"Is it soap? Is it glue? Is it a cloud in a jar?"'
    )
    world.say(
        f"{helper.label} peeked at the label, but the label was crooked, which made the mystery even funnier."
    )


def reveal(world: World, helper: Entity, ing: Entity) -> None:
    helper.memes["friendship"] = helper.memes.get("friendship", 0) + 1
    world.say(
        f"Then {helper.label} {HELPERS[helper.id].reveal}, and everyone blinked."
    )
    world.say(
        f'"It is lard," {helper.label.lower()} said. "Not a monster. Not even a mouse."'
    )


def transform(world: World, hero: Entity, ing: Entity, helper: Entity) -> None:
    ing.state = "mixed"
    ing.meters["warmth"] = ing.meters.get("warmth", 0) + 1
    world.say(
        f"They mixed the lard into the dough, and the blob stopped being a blob."
    )
    world.say(
        f"After the oven did its hot little trick, {HELPERS[helper.id].result}."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0) + 1
    helper.memes["friendship"] = helper.memes.get("friendship", 0) + 1


def ending(world: World, hero: Entity, helper: Entity, ing: Entity) -> None:
    world.say(
        f"{hero.id} laughed because the scary-looking jar had become a delicious surprise, "
        f"and the best part was making it together."
    )
    world.say(
        f"At the end, {hero.id} had flaky crumbs on {hero.pronoun('possessive')} chin, "
        f"and {helper.label.lower()} had the proud smile of a very helpful friend."
    )


def tell(setting: Setting, ingredient: Ingredient, helper: Helper, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"trait": trait}))
    pal = world.add(Entity(id=helper.id, kind="character", type="adult", label=helper.label, meters={}, memes={}))
    ing = world.add(Entity(id=ingredient.id, type="ingredient", label=ingredient.label, phrase=ingredient.phrase, state="still"))
    world.facts.update(hero=hero, helper=pal, ingredient=ing, setting=setting)

    intro(world, hero, pal, ing)
    world.para()
    suspense(world, hero, pal, ing)
    world.para()
    reveal(world, pal, ing)
    transform(world, hero, ing, pal)
    world.para()
    ending(world, hero, pal, ing)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, ing = f["hero"], f["helper"], f["ingredient"]
    return [
        f'Write a short comedy story for a child where {hero.id} finds {ing.label} and wonders what it is.',
        f"Tell a funny story about friendship and surprise baking with {ing.label} in {world.setting.place}.",
        f"Write a simple story where a mysterious kitchen ingredient turns into something tasty with help from a friend.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, ing = f["hero"], f["helper"], f["ingredient"]
    return [
        QAItem(
            question=f"What did {hero.id} and {helper.label.lower()} find in the kitchen?",
            answer=f"They found {ing.phrase}. It looked mysterious at first, which made them stare and laugh.",
        ),
        QAItem(
            question=f"Why was the jar funny and suspenseful?",
            answer=f"It was funny because nobody knew what was inside at first, so they guessed silly things before learning it was lard.",
        ),
        QAItem(
            question=f"What changed after they cooked the lard?",
            answer=f"The plain lard changed into a flaky pie crust, and their nervous curiosity changed into happy laughter.",
        ),
        QAItem(
            question=f"How did the friends feel at the end?",
            answer=f"They felt proud and cheerful because they solved the mystery together and made something tasty.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is lard used for in baking?",
            answer="Lard can be used to make pastries and pie crusts flaky and tender.",
        ),
        QAItem(
            question="Why does mixing with a friend make work more fun?",
            answer="When friends help each other, the job feels lighter, and they can laugh together while they work.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new form, like a blob of dough becoming a pie crust.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} kind={e.kind:9} type={e.type:10} state={e.state or '-'} "
            f"meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", ingredient="lard", helper="grandma", name="Maya", gender="girl", trait="curious"),
    StoryParams(place="bakery", ingredient="lard", helper="friend", name="Noah", gender="boy", trait="silly"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about lard, suspense, friendship, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--ingredient", choices=INGREDIENTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.ingredient and args.ingredient != "lard":
        raise StoryError(explain_rejection(INGREDIENTS[args.ingredient]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.ingredient is None or c[1] == args.ingredient)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, ingredient, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice([n for n, g in HEROES if g == gender])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, ingredient=ingredient, helper=helper, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], INGREDIENTS[params.ingredient], HELPERS[params.helper], params.name, params.gender, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3.\n#show friendship_story/1.\n#show transformation_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.name}: {p.ingredient} in {p.place} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
