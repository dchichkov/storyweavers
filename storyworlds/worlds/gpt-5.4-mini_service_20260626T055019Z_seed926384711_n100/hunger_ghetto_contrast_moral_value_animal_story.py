#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/hunger_ghetto_contrast_moral_value_animal_story.py
================================================================================================

A small Animal-Story-style world about hunger, a ghetto neighborhood, and a
strong contrast between selfishness and moral value.

Premise:
- Two animal neighbors live in a cramped city block.
- One is hungry and has little food.
- A contrast arises when one animal hoards a snack while the other chooses to share.
- The ending proves the moral value: kindness feeds more than one belly.

The world is intentionally simple and constraint-driven:
- The story is grounded in physical state (food, distance, ownership, hunger).
- Emotional state matters too (kindness, shame, gratitude, greed).
- The ending is a causal resolution, not a frozen moral slogan.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    species: str = "thing"
    name: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    neighborhood: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    neighborhood: str
    hero: str
    neighbor: str
    food: str
    seed: Optional[int] = None


NEIGHBORHOODS = {
    "alley": "the narrow alley by the market",
    "block": "the crowded apartment block",
    "courtyard": "the cracked courtyard behind the shops",
}

HEROES = [
    ("Milo", "mouse"),
    ("Tala", "cat"),
    ("Ravi", "rabbit"),
    ("Pip", "bird"),
    ("Nina", "fox"),
]

NEIGHBORS = [
    ("Benny", "bear"),
    ("Lulu", "dog"),
    ("Oona", "otter"),
    ("Suri", "squirrel"),
    ("Timo", "turtle"),
]

FOODS = [
    "a loaf of bread",
    "a warm bun",
    "a bowl of porridge",
    "two apples",
    "a small bag of rice cakes",
]

MORAL_VALUES = [
    "kindness",
    "sharing",
    "care",
    "fairness",
    "generosity",
]


class StoryWorld(World):
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal Story world about hunger, ghetto contrast, and moral value."
    )
    ap.add_argument("--neighborhood", choices=NEIGHBORHOODS)
    ap.add_argument("--hero")
    ap.add_argument("--neighbor")
    ap.add_argument("--food")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for n in NEIGHBORHOODS:
        for h, _ in HEROES:
            for food in FOODS:
                combos.append((n, h, food))
    return combos


def explain_invalid(msg: str) -> str:
    return f"(No story: {msg})"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    neighborhood = args.neighborhood or rng.choice(list(NEIGHBORHOODS))
    hero = args.hero or rng.choice([h for h, _ in HEROES])
    neighbor = args.neighbor or rng.choice([n for n, _ in NEIGHBORS if n != hero])
    food = args.food or rng.choice(FOODS)
    return StoryParams(neighborhood=neighborhood, hero=hero, neighbor=neighbor, food=food)


def _hunger_word(level: float) -> str:
    if level >= 2:
        return "very hungry"
    if level >= 1:
        return "hungry"
    return "full"


def tell(params: StoryParams) -> StoryWorld:
    world = StoryWorld(NEIGHBORHOODS[params.neighborhood])

    hero_species = next(s for h, s in HEROES if h == params.hero)
    neighbor_species = next(s for n, s in NEIGHBORS if n == params.neighbor)

    hero = world.add(Entity(id="hero", kind="character", species=hero_species, name=params.hero))
    neighbor = world.add(Entity(id="neighbor", kind="character", species=neighbor_species, name=params.neighbor))
    food = world.add(Entity(id="food", species="food", name=params.food, owner="hero"))
    spare = world.add(Entity(id="spare", species="food", name="half", owner="neighbor"))

    hero.meters["hunger"] = 2.0
    neighbor.meters["hunger"] = 1.0
    hero.memes["hope"] = 1.0
    neighbor.memes["greed"] = 1.0

    # Act 1
    world.say(
        f"In {world.neighborhood}, {hero.name} the {hero.species} lived beside {neighbor.name} the {neighbor.species}."
    )
    world.say(
        f"It was a hard little place with thin walls, little crumbs, and long evenings when bellies growled."
    )
    world.say(
        f"{hero.name} was {_hunger_word(hero.meters['hunger'])}, and {hero.name} kept looking at {food.name} on the shelf."
    )

    world.para()

    # Act 2: contrast
    world.say(
        f"That morning, {neighbor.name} found {food.name} and pulled it close with a quick, selfish grin."
    )
    world.say(
        f"{hero.name} asked for a bite, but {neighbor.name} turned away and said, 'Mine.'"
    )
    hero.memes["sadness"] = 1.0
    neighbor.memes["pride"] = 1.0
    world.say(
        f"The contrast was plain: one belly was empty, and the other was full of want more than need."
    )

    world.para()

    # Turn
    world.say(
        f"Then {hero.name} noticed a little chick nearby, too small to reach the street stall."
    )
    world.say(
        f"Even while hungry, {hero.name} split a crumb from a saved snack and passed it over."
    )
    hero.meters["hunger"] -= 0.5
    hero.memes["kindness"] = 1.0
    world.say(
        f"The chick pecked happily, and {neighbor.name} stared at the small, brave choice."
    )

    # Resolution
    if neighbor.meters["hunger"] >= THRESHOLD and hero.memes["kindness"] >= THRESHOLD:
        neighbor.memes["shame"] = 1.0
        neighbor.memes["gratitude"] = 1.0
        neighbor.meters["hunger"] -= 1.0
        food.owner = "both"
        world.say(
            f"At last, {neighbor.name}'s face softened. The hiding stopped, and {neighbor.name} broke {food.name} in two."
        )
        world.say(
            f"{hero.name} and {neighbor.name} shared the last bites, and the alley felt warmer than before."
        )
        world.say(
            f"Their biggest meal was not just the food; it was learning that moral value can fill a room."
        )
    else:
        world.say(
            f"By sunset, {hero.name} still had little, but the day had already shown what kind of animal {hero.name} wanted to be."
        )

    world.facts.update(
        hero=hero,
        neighbor=neighbor,
        food=food,
        spare=spare,
        neighborhood=params.neighborhood,
        moral_value="sharing",
        contrast=True,
        hunger=True,
    )
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    hero = f["hero"]
    neighbor = f["neighbor"]
    return [
        "Write a short Animal Story about hunger in a ghetto neighborhood, where a kind choice creates a strong contrast with greed.",
        f"Tell a gentle story about {hero.name} and {neighbor.name} in {world.neighborhood} that ends with a moral value about sharing.",
        "Write a child-friendly story where one hungry animal is tempted to keep food, but a wiser choice changes the ending.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    neighbor = f["neighbor"]
    food = f["food"]
    return [
        QAItem(
            question=f"Who was hungry in the story?",
            answer=f"{hero.name} was hungry in the story, and the little neighborhood made that hunger feel even sharper.",
        ),
        QAItem(
            question=f"What made the story show a contrast?",
            answer=f"The contrast came from {neighbor.name} hoarding {food.name} while {hero.name} chose to share with a smaller animal.",
        ),
        QAItem(
            question="What moral value did the story show?",
            answer="The story showed the moral value of sharing, because kindness helped more than selfishness did.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"At the end, {hero.name} and {neighbor.name} shared the food, and the place felt warmer and kinder.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What does hunger mean?",
            answer="Hunger means your body wants food because it needs energy.",
        ),
        QAItem(
            question="What is a contrast?",
            answer="A contrast is when two things are very different, like sharing and hoarding.",
        ),
        QAItem(
            question="Why is kindness a moral value?",
            answer="Kindness is a moral value because it helps other people and makes life better for everyone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id}: {e.name or e.species} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
valid(N,H,F) :- neighborhood(N), hero(H), food(F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for n in NEIGHBORHOODS:
        lines.append(asp.fact("neighborhood", n))
    for h, _ in HEROES:
        lines.append(asp.fact("hero", h))
    for f in FOODS:
        lines.append(asp.fact("food", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


def build_story_sample(params: StoryParams) -> StorySample:
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


CURATED = [
    StoryParams(neighborhood="block", hero="Milo", neighbor="Benny", food="a loaf of bread"),
    StoryParams(neighborhood="alley", hero="Tala", neighbor="Lulu", food="a bowl of porridge"),
    StoryParams(neighborhood="courtyard", hero="Ravi", neighbor="Suri", food="two apples"),
]


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        neighborhood=args.neighborhood or rng.choice(list(NEIGHBORHOODS)),
        hero=args.hero or rng.choice([h for h, _ in HEROES]),
        neighbor=args.neighbor or rng.choice([n for n, _ in NEIGHBORS]),
        food=args.food or rng.choice(FOODS),
    )


def generate(params: StoryParams) -> StorySample:
    return build_story_sample(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_story_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} in {p.neighborhood}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
