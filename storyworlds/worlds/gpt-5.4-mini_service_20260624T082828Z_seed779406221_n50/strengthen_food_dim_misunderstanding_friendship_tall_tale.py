#!/usr/bin/env python3
"""
A tiny Tall Tale storyworld about a mighty kindness, a food-dim misunderstanding,
and friendship that grows stronger when the facts are finally seen plain.
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
class StoryParams:
    place: str
    hero: str
    friend: str
    food: str
    misunderstanding: str
    seed: Optional[int] = None


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    hero: Character
    friend: Character
    food: str
    misunderstanding: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "prairie": "the wide prairie",
    "riverbend": "the river bend",
    "hilltown": "the hill town",
    "canyon": "the dusty canyon",
}

HEROES = [
    ("Mabel", "girl"),
    ("Hank", "boy"),
    ("Juniper", "girl"),
    ("Otis", "boy"),
    ("Ada", "girl"),
    ("Bram", "boy"),
]

FRIENDS = [
    ("Pepper", "friend"),
    ("Milo", "friend"),
    ("Nell", "friend"),
    ("Pip", "friend"),
    ("Daisy", "friend"),
    ("Wren", "friend"),
]

FOODS = {
    "cornbread": {
        "phrase": "a pan of cornbread",
        "dim": "food-dim",
        "strengthen": "strengthen",
        "crumb": "crumbly",
    },
    "apple_pie": {
        "phrase": "a warm apple pie",
        "dim": "food-dim",
        "strengthen": "strengthen",
        "crumb": "sugary",
    },
    "bean_stew": {
        "phrase": "a big pot of bean stew",
        "dim": "food-dim",
        "strengthen": "strengthen",
        "crumb": "steamy",
    },
    "honey_bread": {
        "phrase": "a loaf of honey bread",
        "dim": "food-dim",
        "strengthen": "strengthen",
        "crumb": "golden",
    },
}

MISUNDERSTANDINGS = {
    "shadow": "a long shadow made the food look dim and strange",
    "dust": "a puff of dust dimmed the food and made it look spoiled",
    "smoke": "a little smoke dimmed the food and made it look dark",
    "moonlight": "the moonlight made the food look dim and silvery instead of bright",
}

GIRL_NAMES = [n for n, g in HEROES if g == "girl"]
BOY_NAMES = [n for n, g in HEROES if g == "boy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld: strengthen food-dim misunderstanding friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
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
    hero = args.hero or rng.choice([n for n, _ in HEROES])
    friend = args.friend or rng.choice([n for n, _ in FRIENDS if n != hero])
    food = args.food or rng.choice(list(FOODS))
    misunderstanding = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    place = args.place or rng.choice(list(PLACES))
    if hero == friend:
        raise StoryError("The hero and friend must be different people.")
    return StoryParams(place=place, hero=hero, friend=friend, food=food, misunderstanding=misunderstanding)


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a tall tale for a young child about friendship, a {world.food}, and a food-dim misunderstanding.',
        f"Tell a simple story where {world.facts['hero']} and {world.facts['friend']} almost argue, but then strengthen their friendship.",
        f'Use the phrase "{world.misunderstanding}" and end with everyone happy about the food.',
    ]


def _make_world(params: StoryParams) -> World:
    hero = Character(name=params.hero, role="hero")
    friend = Character(name=params.friend, role="friend")
    return World(
        place=PLACES[params.place],
        hero=hero,
        friend=friend,
        food=params.food,
        misunderstanding=MISUNDERSTANDINGS[params.misunderstanding],
    )


def _story(world: World) -> None:
    food = FOODS[world.food]
    hero = world.hero
    friend = world.friend

    hero.memes["pride"] = 1
    hero.memes["care"] = 1
    friend.memes["hope"] = 1

    world.say(
        f"Out on {world.place}, {hero.name} had a laugh as big as a barn door and a heart that could hold a wagonload of kindness."
    )
    world.say(
        f"{hero.name} carried {food['phrase']} to a picnic table, and {friend.name} came trotting along, hungry as a hound after supper."
    )

    world.para()
    hero.memes["worry"] = 1
    friend.memes["surprise"] = 1
    hero.meters["food_dim"] = 1
    world.facts["food_dim"] = True
    world.facts["mismatch"] = food["dim"]
    world.say(
        f"Then {world.misunderstanding.lower()}, so the feast looked dim as an old lantern and the two friends stared like they had seen a cloud swallow the moon."
    )
    world.say(
        f"{friend.name} thought the dark look meant the food was no good, and {hero.name} thought {friend.name} was turning away from the table."
    )

    world.para()
    hero.memes["misunderstanding"] = 1
    friend.memes["misunderstanding"] = 1
    hero.meters["strengthen"] = 1
    friend.meters["strengthen"] = 1
    world.say(
        f"{hero.name} stood tall as a fence post and said, 'I brought it for us, not to fool you!'"
    )
    world.say(
        f"Then {friend.name} leaned in close and saw the truth: the food was only dimmed by the {world.misunderstanding.split()[0]}, not ruined one bit."
    )

    world.para()
    hero.memes["joy"] = 2
    friend.memes["joy"] = 2
    hero.memes["friendship"] = 2
    friend.memes["friendship"] = 2
    world.facts["resolved"] = True
    world.say(
        f"With a mighty grin, {friend.name} took a bite and hollered that it tasted as fine as sunrise."
    )
    world.say(
        f"The two friends laughed, shared the rest of the {food['crumb']} feast, and their friendship grew so strong it felt fit to anchor a cloud."
    )


def story_qa(world: World) -> list[QAItem]:
    hero = world.hero.name
    friend = world.friend.name
    return [
        QAItem(
            question=f"Why did {friend} think the food might be bad at first?",
            answer=f"{friend} thought the food might be bad because {world.misunderstanding.lower()} made it look dim and strange.",
        ),
        QAItem(
            question=f"What did {hero} want to happen with the food?",
            answer=f"{hero} wanted to share the food with {friend} and keep the friendship strong.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"At the end, the misunderstanding was cleared up, the food was fine, and the friendship grew stronger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to strengthen something?",
            answer="To strengthen something means to make it stronger, firmer, or harder to break.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think the wrong thing about what is happening.",
        ),
        QAItem(
            question="Why do people share food with friends?",
            answer="People share food with friends to be kind, to enjoy the meal together, and to show friendship.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for c in [world.hero, world.friend]:
        lines.append(f"  {c.name:8} role={c.role} meters={dict(c.meters)} memes={dict(c.memes)}")
    lines.append(f"  food={world.food} place={world.place}")
    lines.append(f"  misunderstanding={world.misunderstanding}")
    return "\n".join(lines)


ASP_RULES = r"""
food_dim(F) :- food(F), dim_fact(F).
misunderstanding(M) :- misunderstanding_fact(M).
resolve(F,M) :- food_dim(F), misunderstanding(M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for food, cfg in FOODS.items():
        lines.append(asp.fact("food", food))
        lines.append(asp.fact("dim_fact", food))
        lines.append(asp.fact("strengthen_word", cfg["strengthen"]))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding_fact", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show resolve/2."))
    clingo_pairs = sorted(set(asp.atoms(model, "resolve")))
    python_pairs = sorted((food, m) for food in FOODS for m in MISUNDERSTANDINGS)
    if clingo_pairs == python_pairs:
        print(f"OK: clingo gate matches python ({len(clingo_pairs)} combinations).")
        return 0
    print("MISMATCH between clingo and python.")
    print("clingo:", clingo_pairs)
    print("python:", python_pairs)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    world.facts.update(
        hero=world.hero.name,
        friend=world.friend.name,
        food=params.food,
        misunderstanding=world.misunderstanding,
        place=world.place,
    )
    _story(world)
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


CURATED = [
    StoryParams(place="prairie", hero="Mabel", friend="Pepper", food="cornbread", misunderstanding="shadow"),
    StoryParams(place="riverbend", hero="Hank", friend="Nell", food="apple_pie", misunderstanding="dust"),
    StoryParams(place="hilltown", hero="Juniper", friend="Pip", food="bean_stew", misunderstanding="smoke"),
    StoryParams(place="canyon", hero="Ada", friend="Wren", food="honey_bread", misunderstanding="moonlight"),
]


def resolve_all(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    if args.all:
        return CURATED
    return [resolve_params(args, random.Random((args.seed or 0) + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolve/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show resolve/2."))
        print(sorted(set(asp.atoms(model, "resolve"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero} and {p.friend} at {p.place} ({p.food})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
