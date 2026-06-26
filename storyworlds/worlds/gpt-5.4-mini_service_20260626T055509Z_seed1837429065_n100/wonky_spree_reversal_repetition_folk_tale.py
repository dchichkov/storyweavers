#!/usr/bin/env python3
"""
A tiny folk-tale storyworld with a wonky little spree and a reversal.

Seed tale:
---
In a small village by the pine trees, a clever child found a wonky cart with one
wheel that wobbled. The child set off on a spree to gather bright things for the
market: apples, ribbons, and a bell. Each time the cart bumped, it jangled and
tilted, but the child laughed and kept going: one apple, two apples, three apples.

At the river path, the wind spun the cart around. Suddenly the "wonky" wheel was
the brave one, because it kept the cart from tipping into the water. The child
looked again and saw that the little cart was not broken after all; it was only
odd, and odd things can be useful. So the child turned back with a neat load,
and the village praised the day that began as a wobble and ended as a gift.

World design:
- A child and a companion move through a small village, market lane, and river path.
- A wonky cart causes a repeated, child-friendly spree of gathering.
- A reversal turns the weakness into a strength.
- Repetition is used in the story prose, and state changes drive the ending image.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    sparkle: str = ""


@dataclass
class StoryParams:
    name: str
    gender: str
    companion: str
    place: str
    prize: str
    seed: Optional[int] = None


class World:
    def __init__(self, village: Place, lane: Place, river: Place):
        self.places = {"village": village, "lane": lane, "river": river}
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.wonky = False
        self.spree_count = 0
        self.reversal = False
        self.events: list[str] = []

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

    def copy(self) -> "World":
        import copy
        clone = World(self.places["village"], self.places["lane"], self.places["river"])
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.wonky = self.wonky
        clone.spree_count = self.spree_count
        clone.reversal = self.reversal
        clone.events = list(self.events)
        return clone


VILLAGE = Place("village", "the little village", "village")
LANE = Place("lane", "the market lane", "lane")
RIVER = Place("river", "the river path", "river")

PRIZES = {
    "apples": ObjectSpec("apples", "red apples", "three bright red apples", "shiny"),
    "ribbons": ObjectSpec("ribbons", "ribbons", "three ribbon loops", "bright"),
    "bell": ObjectSpec("bell", "a brass bell", "a small brass bell", "clear"),
}

NAMES = {
    "girl": ["Mira", "Nina", "Lina", "Tessa", "Sana"],
    "boy": ["Pavel", "Bram", "Toma", "Eli", "Nico"],
}

COMPANIONS = ["grandmother", "father", "brother", "sister", "neighbor"]


def _folk_refrain(n: int, obj: str) -> str:
    if n == 1:
        return f"one {obj}"
    if n == 2:
        return f"two {obj}"
    return f"three {obj}"


def _spree_phrase(count: int, prize: ObjectSpec) -> str:
    return _folk_refrain(count, prize.label)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale world: wonky cart, spree, reversal, repetition.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--place", choices=["village", "lane", "river"], default="village")
    ap.add_argument("--prize", choices=list(PRIZES), default="apples")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(
        name=name,
        gender=gender,
        companion=companion,
        place=args.place or "village",
        prize=args.prize or "apples",
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.prize not in PRIZES:
        raise StoryError("unknown prize")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("unknown gender")


ASP_RULES = r"""
place(village). place(lane). place(river).
prize(apples). prize(ribbons). prize(bell).
gender(girl). gender(boy).

wonky_cart(village).
spree(village, lane, river).
reversal(river).

#show valid_story/4.
valid_story(P, G, PR, C) :- place(P), gender(G), prize(PR), companion(C),
    wonky_cart(P), spree(P, lane, river), reversal(river).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in ["village", "lane", "river"]:
        lines.append(asp.fact("place", p))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender", g))
    for c in COMPANIONS:
        lines.append(asp.fact("companion", c))
    lines.append(asp.fact("wonky_cart", "village"))
    lines.append(asp.fact("spree", "village", "lane", "river"))
    lines.append(asp.fact("reversal", "river"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set((("village", g, p, c) for g in ["girl", "boy"] for p in PRIZES for c in COMPANIONS))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates")
    return 1


def generate_story(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    companion = world.add(Entity(id="Companion", kind="character", type=params.companion, label=params.companion))
    cart = world.add(Entity(id="cart", type="cart", label="wonky cart", phrase="a wonky little cart"))
    prize = PRIZES[params.prize]
    goods = world.add(Entity(id=prize.id, type="goods", label=prize.label, phrase=prize.phrase, owner=hero.id, carried_by=hero.id))

    world.wonky = True
    hero.memes["curiosity"] = 1
    hero.memes["joy"] = 1
    world.say(f"{hero.id} lived in {VILLAGE.label}, where the pine trees bowed and the wind sang softly.")
    world.say(f"One morning, {hero.id} found {cart.phrase} by the lane, and the cart had a wheel that wobbled and waggled.")
    world.say(f"{hero.id} smiled, for a wonky thing can still be a good thing, and off {hero.pronoun('subject')} went on a spree.")

    world.para()
    world.say(f"{hero.id} gathered { _spree_phrase(1, prize) }, then { _spree_phrase(2, prize) }, then { _spree_phrase(3, prize)}.")
    world.say(f"One by one, one by one, {hero.id} loaded the cart while {companion.label} watched and hummed.")
    world.spree_count = 3
    cart.meters["load"] = 3
    goods.meters["gathered"] = 3

    world.para()
    world.say(f"The cart bumped along the market lane: bump, bump, bump; wobble, wobble, wobble.")
    world.say(f"Then the path bent to the river, and the wind gave one sharp twist.")
    world.say(f"The cart lurched toward the water, and everyone cried out, but the wonky wheel dug in deep.")
    world.reversal = True
    cart.memes["brave"] = 1
    cart.meters["stability"] = 1
    world.say(f"That was the reversal: the wheel that seemed the worst was the wheel that saved the day.")

    world.para()
    hero.memes["relief"] = 1
    companion.memes["wonder"] = 1
    world.say(f"{hero.id} laughed, because odd things are not always broken things.")
    world.say(f"{hero.id} and {companion.label} turned back to {VILLAGE.label} with the cart straight and the load neat and safe.")
    world.say(f"And so the village had its apples, and ribbons, and bell, and the folk still tell how a wobble became a blessing.")

    world.facts.update(hero=hero, companion=companion, cart=cart, goods=goods, prize=prize, params=params)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    companion = f["companion"]
    return [
        QAItem(
            question=f"What did {hero.id} find by the lane?",
            answer=f"{hero.id} found a wonky little cart with one wheel that wobbled and waggled.",
        ),
        QAItem(
            question=f"What did {hero.id} gather on the spree?",
            answer=f"{hero.id} gathered {prize.phrase}, then more and more, until the cart was full enough to carry home.",
        ),
        QAItem(
            question=f"What was the reversal at the river path?",
            answer=f"The reversal was that the wonky wheel, which looked like a problem, kept the cart from tipping into the river.",
        ),
        QAItem(
            question=f"Who went back to the village with {hero.id}?",
            answer=f"{companion.label} went back with {hero.id}, and together they returned to the village with the load kept safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does wonky mean?",
            answer="Wonky means a little crooked, uneven, or wobbly, like something that does not stand quite straight.",
        ),
        QAItem(
            question="What is a spree?",
            answer="A spree is a busy stretch of doing something again and again, often with excitement.",
        ),
        QAItem(
            question="What is a reversal in a story?",
            answer="A reversal is a turn where the situation changes in an unexpected way, often from trouble to help.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    return [
        f"Write a folk tale about {hero.id}, a wonky cart, and a spree of gathering {prize.label}.",
        f"Tell a child-friendly story with repetition: bump, wobble, and a happy reversal.",
        "Write a short folk tale where something that seems broken turns out to be useful.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"wonky={world.wonky} spree_count={world.spree_count} reversal={world.reversal}")
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(VILLAGE, LANE, RIVER)
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(name="Mira", gender="girl", companion="grandmother", place="village", prize="apples"),
    StoryParams(name="Pavel", gender="boy", companion="father", place="village", prize="ribbons"),
    StoryParams(name="Nina", gender="girl", companion="neighbor", place="village", prize="bell"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
