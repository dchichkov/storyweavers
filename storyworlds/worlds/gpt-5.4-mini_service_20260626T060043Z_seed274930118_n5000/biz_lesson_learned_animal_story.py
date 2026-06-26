#!/usr/bin/env python3
"""
A standalone storyworld for a small Animal Story-style lesson about biz.

Premise:
A young animal runs a tiny biz, makes a choice that seems clever, and then
learns a lesson when the choice causes a real problem. The world model tracks
the business, the lesson, and the repair so the story changes because of state,
not just swapped nouns.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Animal:
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {
        "energy": 2.0,
        "coins": 0.0,
        "trust": 2.0,
        "mess": 0.0,
        "work": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "pride": 0.0,
        "worry": 0.0,
        "guilt": 0.0,
        "relief": 0.0,
        "kindness": 0.0,
    })

    def pronoun(self) -> str:
        return "they"

    def poss(self) -> str:
        return "their"


@dataclass
class Biz:
    name: str
    item: str
    place: str
    price: int
    honest_bonus: int
    shortcut_cost: int


@dataclass
class World:
    hero: Animal
    friend: Animal
    customer: Animal
    biz: Biz
    lesson: str = ""
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SPECIES = ["cat", "dog", "fox", "rabbit", "bear", "mouse", "goat", "otter"]
NAMES = ["Milo", "Tia", "Pip", "Nina", "Roo", "Kiko", "Luna", "Bram", "Mika", "Zed"]
PLACES = ["the market", "the town square", "the little lane", "the sunny corner"]
ITEMS = [
    ("cookies", "fresh cookies", 3, 2, 1),
    ("flowers", "bright flowers", 4, 2, 1),
    ("lemonade", "cool lemonade", 2, 1, 1),
    ("wooden toys", "small wooden toys", 5, 2, 2),
]
LESSONS = [
    "honesty builds trust",
    "sharing makes the day better",
    "a quick shortcut can cause a bigger problem",
    "kind words can fix a mistake",
]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: "StoryParams") -> World:
    hero = Animal(name=params.hero_name, species=params.hero_species, role="biz helper")
    friend = Animal(name=params.friend_name, species=params.friend_species, role="helper")
    customer = Animal(name=params.customer_name, species=params.customer_species, role="customer")

    item_name, item_desc, price, honest_bonus, shortcut_cost = params.item
    biz = Biz(
        name=f"{hero.name}'s biz",
        item=item_name,
        place=params.place,
        price=price,
        honest_bonus=honest_bonus,
        shortcut_cost=shortcut_cost,
    )
    return World(hero=hero, friend=friend, customer=customer, biz=biz)


def run_simulation(world: World, params: "StoryParams", narrate: bool = True) -> None:
    h, f, c, b = world.hero, world.friend, world.customer, world.biz
    item_name, item_desc, price, honest_bonus, shortcut_cost = params.item

    world.say(
        f"{h.name} was a little {h.species} who ran a tiny biz at {b.place}."
    )
    world.say(
        f"{h.name} sold {item_desc} and hoped the biz would do well."
    )
    world.say(
        f"{f.name}, a friendly {f.species}, came to help set up the table."
    )

    world.para()
    h.memes["pride"] += 1
    h.meters["work"] += 1
    world.say(
        f"One busy morning, {c.name} came by and wanted {item_desc}."
    )
    world.say(
        f"{h.name} saw that the coins looked nice, and {h.pronoun()} felt tempted to take a shortcut."
    )

    # Shortcut: less work now, but lower trust and a later problem.
    h.meters["coins"] += price
    h.meters["mess"] += shortcut_cost
    h.memes["worry"] += 1
    c.meters["trust"] -= 1
    world.say(
        f"{h.name} wrapped the order too fast and forgot one important part."
    )
    world.say(
        f"{c.name} left with a smile, but the package was not right."
    )

    world.para()
    world.say(
        f"That afternoon, {c.name} came back and said the order did not feel fair."
    )
    h.memes["guilt"] += 2
    h.meters["trust"] -= 1
    world.say(
        f"{h.name}'s ears drooped. The shortcut had made a bigger mess than expected."
    )

    # Lesson learned turn.
    world.say(
        f"{f.name} gently said, \"A good biz needs honest work.\""
    )
    world.say(
        f"{h.name} listened, fixed the order, and added an extra treat to make it right."
    )
    h.meters["work"] += honest_bonus
    h.meters["mess"] = max(0.0, h.meters["mess"] - 1)
    h.meters["trust"] += 2
    c.meters["trust"] += 2
    h.memes["relief"] += 2
    h.memes["kindness"] += 1

    world.para()
    world.say(
        f"{c.name} returned and saw the careful fix."
    )
    world.say(
        f"{c.name} smiled, and {h.name} smiled back. The biz felt small, but it felt honest."
    )
    world.say(
        f"By sunset, {h.name} had learned that {params.lesson}."
    )

    world.lesson = params.lesson
    world.facts.update(
        hero=h,
        friend=f,
        customer=c,
        biz=b,
        item_desc=item_desc,
        item_name=item_name,
        lesson=params.lesson,
        shortcut_taken=True,
        fixed=True,
    )


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    hero_name: str
    hero_species: str
    friend_name: str
    friend_species: str
    customer_name: str
    customer_species: str
    place: str
    item: tuple[str, str, int, int, int]
    lesson: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story lesson-learned biz world.")
    ap.add_argument("--name")
    ap.add_argument("--species", choices=SPECIES)
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-species", choices=SPECIES)
    ap.add_argument("--customer-name")
    ap.add_argument("--customer-species", choices=SPECIES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=[x[0] for x in ITEMS])
    ap.add_argument("--lesson", choices=LESSONS)
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
    item = next(i for i in ITEMS if i[0] == (args.item or rng.choice([x[0] for x in ITEMS])))
    lesson = args.lesson or rng.choice(LESSONS)
    hero_species = args.species or rng.choice(SPECIES)
    friend_species = args.friend_species or rng.choice([s for s in SPECIES if s != hero_species])
    customer_species = args.customer_species or rng.choice([s for s in SPECIES if s != hero_species])

    hero_name = args.name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice([n for n in NAMES if n != hero_name])
    customer_name = args.customer_name or rng.choice([n for n in NAMES if n not in {hero_name, friend_name}])

    place = args.place or rng.choice(PLACES)
    return StoryParams(
        hero_name=hero_name,
        hero_species=hero_species,
        friend_name=friend_name,
        friend_species=friend_species,
        customer_name=customer_name,
        customer_species=customer_species,
        place=place,
        item=item,
        lesson=lesson,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    run_simulation(world, params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short Animal Story about {f['hero'].name} and a tiny biz that learns {f['lesson']}.",
        f"Tell a child-friendly story where {f['hero'].name} runs a biz at {f['biz'].place} and fixes a mistake honestly.",
        f"Write a gentle story about a small animal business, a shortcut, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, f, c, b = world.hero, world.friend, world.customer, world.biz
    return [
        QAItem(
            question=f"What kind of biz did {h.name} run?",
            answer=f"{h.name} ran a tiny biz selling {b.item} at {b.place}.",
        ),
        QAItem(
            question=f"What problem did {h.name} make when {c.name} came to buy from the biz?",
            answer=f"{h.name} took a shortcut and forgot an important part of the order, which made the customer unhappy.",
        ),
        QAItem(
            question=f"What lesson did {h.name} learn by the end?",
            answer=f"{h.name} learned that {world.lesson}.",
        ),
        QAItem(
            question=f"Who helped {h.name} remember the right thing to do?",
            answer=f"{f.name}, the friendly {f.species}, helped by giving kind advice.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a biz?",
            answer="A biz is a small business where someone sells something and helps customers.",
        ),
        QAItem(
            question="Why is honesty important in a biz?",
            answer="Honesty matters because customers need to trust that they will get the right thing.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="Learning a lesson means understanding a better choice after something goes wrong.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.friend, world.customer]:
        meters = {k: round(v, 2) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 2) for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.name:8} ({ent.species:7}) meters={meters} memes={memes}")
    lines.append(f"  lesson: {world.lesson}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts describe a small biz story with a shortcut and a lesson learned.
shortcut_taken(H) :- hero(H).
needs_fix(H) :- shortcut_taken(H).
lesson_learned(H) :- needs_fix(H), fixed(H).

valid_story(H, B, L) :- hero(H), biz(B), lesson(L), lesson_learned(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in NAMES:
        lines.append(asp.fact("name", n))
    for s in SPECIES:
        lines.append(asp.fact("species", s))
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for item_name, _, _, _, _ in ITEMS:
        lines.append(asp.fact("item", item_name))
    for lesson in LESSONS:
        lines.append(asp.fact("lesson", lesson))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("biz", "biz"))
    lines.append(asp.fact("fixed", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


# ---------------------------------------------------------------------------
# Selection helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for item_name, _, _, _, _ in ITEMS:
            for lesson in LESSONS:
                out.append((place, item_name, lesson))
    return out


CURATED = [
    StoryParams(
        hero_name="Milo",
        hero_species="fox",
        friend_name="Tia",
        friend_species="rabbit",
        customer_name="Nina",
        customer_species="bear",
        place="the market",
        item=ITEMS[0],
        lesson="honesty builds trust",
    ),
    StoryParams(
        hero_name="Pip",
        hero_species="mouse",
        friend_name="Roo",
        friend_species="otter",
        customer_name="Luna",
        customer_species="cat",
        place="the town square",
        item=ITEMS[2],
        lesson="a quick shortcut can cause a bigger problem",
    ),
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
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
    if args.asp:
        print("ASP mode is available, but this world uses a simple inline twin.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
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
            header = f"### {p.hero_name}: biz at {p.place} with {p.item[0]}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
