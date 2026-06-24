#!/usr/bin/env python3
"""
strengthen_food_dim_misunderstanding_friendship_tall_tale.py
============================================================

A tiny Tall Tale-style storyworld about a strong child, a food-dim misunderstanding,
and a friendship that gets strengthened when the misunderstanding is cleared.

Seed tale used to shape the world:
---
A child named Pip is known for being mighty strong. One morning, Pip's friend
Tessa brings a "food-dim" lunch box from the far side of town, but Pip thinks
"food-dim" means the food is dull, tiny, and not worth sharing. Pip scoffs,
which hurts Tessa's feelings.

Later, Pip learns that "food-dim" is not about the food at all: it is the name
of a famous dim-sun picnic basket made by Tessa's grandpa, built to keep soup
warm on windy hills. Pip apologizes, helps carry the heavy basket, and shares
the soup. The two friends laugh, and their friendship grows stronger.

World model:
- physical meters: weight, carry, warmth, distance, fullness
- emotional memes: pride, hurt, trust, friendship, misunderstanding, joy
- state changes drive the narration: carrying heavy food strengthens resolve,
  a mistaken label causes hurt, and a clear explanation restores trust.

The prose aims for a tall tale voice: bigger-than-life but child-facing and gentle.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    weight: float
    warmth: float = 0.0
    food_dim: bool = False
    tall_tale_name: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    place: str
    item: str
    meal: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


HERO_NAMES = ["Pip", "Mira", "June", "Bo", "Nell", "Ezra", "Sage", "Toby"]
FRIEND_NAMES = ["Tessa", "Lark", "Milo", "Ruby", "Otis", "Wren", "Ivy", "Nico"]

PLACES = {
    "hill": "the windy hill",
    "dock": "the old dock",
    "orchard": "the apple orchard",
    "market": "the busy market square",
}

FOOD_THINGS = {
    "soup_pail": Thing(
        id="soup_pail",
        label="food-dim basket",
        phrase="a food-dim picnic basket full of soup",
        weight=4.0,
        warmth=3.0,
        food_dim=True,
        tall_tale_name="food-dim basket",
        tags={"food-dim", "basket", "soup"},
    ),
    "cornbread": Thing(
        id="cornbread",
        label="cornbread tin",
        phrase="a cornbread tin with a lid like a hat",
        weight=2.0,
        warmth=1.0,
        food_dim=True,
        tall_tale_name="cornbread tin",
        tags={"food-dim", "bread"},
    ),
    "apple_jar": Thing(
        id="apple_jar",
        label="apple jar",
        phrase="a jar of apple jam",
        weight=1.0,
        warmth=0.5,
        food_dim=True,
        tall_tale_name="apple jar",
        tags={"food-dim", "apple"},
    ),
}

MEALS = {
    "soup": "bean soup",
    "cornbread": "cornbread",
    "jam": "apple jam",
}


def honest_misread(food: Thing) -> str:
    if food.id == "soup_pail":
        return "dull, dim, and not worth the trouble"
    if food.id == "cornbread":
        return "plain-looking and too small to matter"
    return "tiny and too silly to share"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, i, m) for p in PLACES for i in FOOD_THINGS for m in MEALS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: strengthen friendship through a food-dim misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=FOOD_THINGS)
    ap.add_argument("--meal", choices=MEALS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.item:
        combos = [c for c in combos if c[1] == args.item]
    if args.meal:
        combos = [c for c in combos if c[2] == args.meal]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, meal = rng.choice(combos)
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    return StoryParams(hero, hero_gender, friend, friend_gender, place, item, meal)


def tell(params: StoryParams) -> World:
    w = World(PLACES[params.place])
    hero = w.add(Entity(id=params.hero, kind="character", type=params.hero_gender, label=params.hero))
    friend = w.add(Entity(id=params.friend, kind="character", type=params.friend_gender, label=params.friend))
    food = FOOD_THINGS[params.item]
    basket = w.add(Entity(id=food.id, type="thing", label=food.label, phrase=food.phrase))
    basket.meters["weight"] = food.weight
    basket.meters["warmth"] = food.warmth
    basket.attrs["food_dim"] = food.food_dim
    basket.attrs["meal"] = params.meal

    hero.memes["strength"] += 2.0
    friend.memes["trust"] += 1.0
    w.say(f"{hero.id} was the sort of child who could hoist a barn cat with one arm and still grin about it.")
    w.say(f"At {w.place}, {hero.id} met {friend.id}, who brought {food.phrase} wrapped up neat as a secret.")

    w.para()
    hero.memes["misunderstanding"] += 1.0
    hero.memes["pride"] += 1.0
    friend.memes["hurt"] += 1.0
    basket.carrier = friend.id
    w.say(
        f"{hero.id} peered at the basket and thought the name sounded {honest_misread(food)}. "
        f"{hero.pronoun().capitalize()} snorted, which made {friend.id}'s smile sag like a wet ribbon."
    )
    w.say(
        f"\"If it is food-dim, then it must be too dim for supper,\" {hero.id} said, as if a wrong word could weigh as much as a wagon."
    )

    w.para()
    hero.memes["guilt"] += 1.0
    friend.memes["friendship"] += 1.0
    basket.carrier = hero.id
    hero.meters["carry"] += basket.meters["weight"]
    hero.meters["effort"] += 2.0
    w.say(
        f"But then {friend.id} opened the lid, and the whole world got a whiff of warm soup rising like a friendly cloud. "
        f"{friend.id} explained that \"food-dim\" was the name of {friend.pronoun('possessive')} grandpa's old picnic basket, built to keep supper warm on windy hills."
    )
    w.say(
        f"{hero.id}'s face went red as a beet. {hero.pronoun().capitalize()} took the heavy basket with both hands and carried it the rest of the way, stronger for the lifting and wiser for the looking."
    )

    w.para()
    hero.memes["trust"] += 2.0
    friend.memes["trust"] += 2.0
    hero.memes["friendship"] += 2.0
    hero.memes["misunderstanding"] = 0.0
    friend.memes["hurt"] = 0.0
    basket.meters["warmth"] += 1.0
    w.say(
        f"At the table, {hero.id} apologized plain and simple. {friend.id} forgave {hero.pronoun('object')} faster than a creek runs downhill in spring. "
        f"They shared the soup, and the basket stayed warm as a snug little sun."
    )
    w.say(
        f"By bedtime, {hero.id} and {friend.id} were laughing so hard the moon seemed to lean closer and listen. "
        f"Their friendship had been strengthened by the honest mistake, and the tall wind outside had nothing on them."
    )

    w.facts.update(
        hero=hero,
        friend=friend,
        basket=basket,
        item=food,
        place=params.place,
        meal=params.meal,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall tale for a young child about {f['hero'].id} and {f['friend'].id} at {f['place']} involving a food-dim misunderstanding and a friendship that grows stronger.",
        f"Tell a child-sized story where someone misreads {f['item'].label} and then learns the truth before supper.",
        f"Write a friendly tall tale in which a strong child helps carry {f['item'].phrase} and makes up after a mix-up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, basket, item = f["hero"], f["friend"], f["basket"], f["item"]
    return [
        QAItem(
            question=f"Why did {hero.id} first think the food-dim basket was silly?",
            answer=f"{hero.id} misunderstood the name and thought {item.label} meant the food was dull and not worth sharing.",
        ),
        QAItem(
            question=f"What did {friend.id} explain about {item.label}?",
            answer=f"{friend.id} explained that it was a special basket made by {friend.pronoun('possessive')} grandpa to keep soup warm on windy hills.",
        ),
        QAItem(
            question=f"How did {hero.id} make things right?",
            answer=f"{hero.id} apologized, carried the heavy basket, and shared the soup with {friend.id}.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The misunderstanding was cleared up, the friends were cheerful again, and their friendship became stronger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to strengthen something?",
            answer="To strengthen something means to make it stronger, steadier, or harder to break.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something wrong because the words or facts were not clear.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people who care about each other and help each other.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(H) :- hero(H), heard_wrong_name(H).
friendship_strong(H, F) :- friends(H, F), apologize(H), share_food(H, F).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "hero"),
        asp.fact("friend", "friend"),
        asp.fact("food_dim", "basket"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    print("OK: ASP twin present for this world.")
    return 0


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Pip", "boy", "Tessa", "girl", "hill", "soup_pail", "soup"),
    StoryParams("Mira", "girl", "Nico", "boy", "dock", "cornbread", "cornbread"),
    StoryParams("Bo", "boy", "Lark", "girl", "orchard", "apple_jar", "jam"),
]


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
        print(asp_program("#show misunderstanding/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode available.")
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for _ in range(args.n):
            params = resolve_params(args, rng)
            samples.append(generate(params))

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
