#!/usr/bin/env python3
"""
A small stand-alone storyworld about a hibachi dinner with rhyme, suspense, and comedy.

Seed premise:
A child goes to a hibachi restaurant expecting a fun meal, but a tiny surprise on the grill creates suspense. The chef's showmanship, a little mix-up, and a friendly fix turn it into a funny evening with a happy ending.
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
    name: str
    parent: str
    chef: str
    friend: str
    dish: str
    garnish: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


NAMES = ["Mina", "Eli", "Nora", "Theo", "Lila", "Jun", "Ari", "Zoe"]
PARENTS = ["mom", "dad", "aunt", "uncle"]
CHEFS = ["Chef Sora", "Chef Bingo", "Chef Nori", "Chef Taro"]
FRIENDS = ["Max", "Pip", "Rae", "Toby", "Momo", "Bea"]
DISHES = ["fried rice", "noodles", "shrimp", "teriyaki chicken", "veggies"]
GARNISHES = ["a lemon wedge", "a tiny onion volcano", "a green pea", "a shiny cherry tomato"]


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

child(N) :- name(N).
parent(P) :- parent_name(P).
chef(C) :- chef_name(C).
friend(F) :- friend_name(F).
dish(D) :- dish_name(D).
garnish(G) :- garnish_name(G).

rhyme_pair(D, G) :- dish_rhyme(D, G).
suspense_pair(D, G) :- suspenseful(D, G).

valid(N, D, G) :- name(N), dish_name(D), garnish_name(G), rhyme_pair(D, G), suspense_pair(D, G).
valid_story(N, D, G, P) :- valid(N, D, G), parent_name(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in NAMES:
        lines.append(asp.fact("name", n))
    for p in PARENTS:
        lines.append(asp.fact("parent_name", p))
    for c in CHEFS:
        lines.append(asp.fact("chef_name", c))
    for f in FRIENDS:
        lines.append(asp.fact("friend_name", f))
    for d in DISHES:
        lines.append(asp.fact("dish_name", d))
    for g in GARNISHES:
        lines.append(asp.fact("garnish_name", g))
    for d, g in RHYMES:
        lines.append(asp.fact("dish_rhyme", d, g))
    for d, g in SUSPENSE:
        lines.append(asp.fact("suspenseful", d, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


RHYMES = [
    ("fried rice", "a green pea"),
    ("noodles", "a tiny onion volcano"),
    ("shrimp", "a lemon wedge"),
    ("teriyaki chicken", "a shiny cherry tomato"),
    ("veggies", "a green pea"),
]
SUSPENSE = [
    ("fried rice", "a tiny onion volcano"),
    ("noodles", "a shiny cherry tomato"),
    ("shrimp", "a tiny onion volcano"),
    ("teriyaki chicken", "a lemon wedge"),
    ("veggies", "a shiny cherry tomato"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A hibachi storyworld with rhyme, suspense, and comedy.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--chef", choices=CHEFS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--garnish", choices=GARNISHES)
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


def valid_combos() -> list[tuple[str, str]]:
    return list(dict.fromkeys(RHYMES))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.dish and args.garnish:
        if (args.dish, args.garnish) not in combos:
            raise StoryError("No story: that dish and garnish do not make a believable rhyme-and-suspense pair.")
    if args.dish:
        combos = [c for c in combos if c[0] == args.dish]
    if args.garnish:
        combos = [c for c in combos if c[1] == args.garnish]
    if not combos:
        raise StoryError("No valid combo matches the given options.")
    dish, garnish = rng.choice(sorted(combos))
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        parent=args.parent or rng.choice(PARENTS),
        chef=args.chef or rng.choice(CHEFS),
        friend=args.friend or rng.choice(FRIENDS),
        dish=dish,
        garnish=garnish,
    )


def generate(params: StoryParams) -> StorySample:
    w = World()
    kid = w.add(Entity(id=params.name, kind="character", label=params.name))
    parent = w.add(Entity(id=params.parent, kind="character", label=params.parent))
    chef = w.add(Entity(id=params.chef, kind="character", label=params.chef))
    friend = w.add(Entity(id=params.friend, kind="character", label=params.friend))
    meal = w.add(Entity(id="meal", label=params.dish, meters={"hot": 0.0}, memes={"tension": 0.0}))
    garnish = w.add(Entity(id="garnish", label=params.garnish, meters={"spin": 0.0}, memes={"surprise": 0.0}))

    w.say(f"{kid.id} went to the hibachi grill with {parent.label}, and the air smelled like butter and fun.")
    w.say(f"{chef.label} said, 'Hold your hats, stay in your seats, and watch the hot pan dance.'")
    w.say(f"{kid.id} laughed because {chef.label} flipped {meal.label} with a grin so bright it could have paid rent.")

    w.para()
    meal.meters["hot"] = 1.0
    meal.memes["tension"] = 1.0
    garnish.meters["spin"] = 1.0
    garnish.memes["surprise"] = 1.0
    w.say(f"Then, with a hiss and a pop, {garnish.label} rolled toward the edge like a tiny runaway moon.")
    w.say(f"{kid.id} gasped. {friend.id} whispered, 'If it drops, it will plop!' and that made everyone snort.")
    w.say(f"{parent.label} reached out, but {chef.label} was quicker and caught it with a spatula like a hero in a silly hat.")

    w.para()
    kid.memes["relief"] = 1.0
    kid.memes["joy"] = 1.0
    chef.memes["pride"] = 1.0
    friend.memes["joy"] = 1.0
    w.say(f"{chef.label} set the garnish on top of the meal and said, 'No flop, just a chop-and-pop!'")
    w.say(f"{kid.id} giggled so hard {kid.id} nearly bounced off the chair, and the whole table joined the rhyme parade.")
    w.say(f"At the end, {kid.id} ate {meal.label} with {garnish.label} on top, and the once-scary little tumble became dinner's funniest trick.")

    w.facts.update(
        kid=kid.id,
        parent=parent.id,
        chef=chef.id,
        friend=friend.id,
        dish=params.dish,
        garnish=params.garnish,
        suspense=True,
        resolved=True,
    )

    prompts = [
        f"Write a funny story about a child at a hibachi restaurant where a small surprise creates suspense.",
        f"Tell a comedy story in which {params.name} visits hibachi with {params.parent} and a chef makes dinner feel like a show.",
        f"Write a child-friendly story that includes {params.dish}, {params.garnish}, and a playful rhyme.",
    ]

    story_qa = [
        QAItem(
            question=f"Who went to the hibachi restaurant in the story?",
            answer=f"{params.name} went with {params.parent}, and they watched {params.chef} cook at the table.",
        ),
        QAItem(
            question=f"What made the moment feel suspenseful?",
            answer=f"{params.garnish} rolled toward the edge of the grill, so everyone had to wait and see if it would fall.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {params.chef} catching the garnish and {params.name} laughing over dinner.",
        ),
        QAItem(
            question=f"Why was the ending funny?",
            answer=f"The chef turned a scary little wobble into a joke and a rhyme, so the whole table laughed.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a hibachi grill?",
            answer="A hibachi grill is a hot cooking surface where a chef cooks food right in front of the diners.",
        ),
        QAItem(
            question="Why do people watch hibachi cooking?",
            answer="People watch hibachi cooking because it is exciting, and the chef often makes the meal feel like a show.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something might go wrong.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like 'pop' and 'flop.'",
        ),
        QAItem(
            question="Why can comedy help a suspenseful scene?",
            answer="Comedy can make a tense moment feel lighter by turning a problem into something silly and fun.",
        ),
    ]

    return StorySample(params=params, story=w.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=w)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(name="Mina", parent="mom", chef="Chef Sora", friend="Max", dish="fried rice", garnish="a green pea"),
        StoryParams(name="Theo", parent="dad", chef="Chef Bingo", friend="Rae", dish="noodles", garnish="a tiny onion volcano"),
        StoryParams(name="Lila", parent="aunt", chef="Chef Nori", friend="Pip", dish="shrimp", garnish="a lemon wedge"),
        StoryParams(name="Jun", parent="uncle", chef="Chef Taro", friend="Toby", dish="teriyaki chicken", garnish="a shiny cherry tomato"),
    ]


CURATED = build_curated()


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (dish, garnish) combos:\n")
        for dish, garnish in triples:
            print(f"  {dish:18} -> {garnish}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
            header = f"### {p.name}: hibachi with {p.dish} and {p.garnish}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
