#!/usr/bin/env python3
"""
A tiny folk-tale storyworld about a tramp, a cliffside business, and a happy ending.

Premise:
- A tramp arrives at a cliff village.
- The tramp wants to earn a living by starting a small business.
- The cliff wind makes the first plan risky.
- A kind helper and a steadier plan lead to a happy ending.

The story is generated from a small world model:
- physical meters: wind, load, coins, repair, safety
- emotional memes: hope, worry, pride, trust, gratitude

The world is intentionally small, classical, and child-facing.
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
# Small world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    name: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def get_meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def set_meter(self, key: str, value: float) -> None:
        self.meters[key] = value

    def bump_meter(self, key: str, delta: float = 1.0) -> None:
        self.meters[key] = self.get_meter(key) + delta

    def get_meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def set_meme(self, key: str, value: float) -> None:
        self.memes[key] = value

    def bump_meme(self, key: str, delta: float = 1.0) -> None:
        self.memes[key] = self.get_meme(key) + delta


@dataclass
class Place:
    name: str = "the cliff village"
    afford_business: bool = True
    windy: bool = True


@dataclass
class Plan:
    id: str
    name: str
    what: str
    risky: str
    safer: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    plan: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

PLACES = {
    "cliff_village": Place(name="the cliff village", afford_business=True, windy=True),
    "harbor_path": Place(name="the harbor path by the cliff", afford_business=True, windy=True),
    "market_square": Place(name="the market square", afford_business=True, windy=False),
}

PLANS = {
    "snack_cart": Plan(
        id="snack_cart",
        name="a little snack cart",
        what="sell warm buns and tea",
        risky="the wind could spill the tea and shake the cart",
        safer="set the cart beside a stone wall and tie the cloth tight",
        keyword="business",
        tags={"business", "food"},
    ),
    "song_stall": Plan(
        id="song_stall",
        name="a song stall",
        what="sing folk songs for pennies",
        risky="the wind could blow away the song sheet",
        safer="hold the song sheet inside a wooden frame",
        keyword="business",
        tags={"business", "song"},
    ),
    "rope_shop": Plan(
        id="rope_shop",
        name="a rope shop",
        what="sell braided ropes to the fishers",
        risky="the cliff path could make the bundles roll away",
        safer="keep the ropes in a basket with a heavy stone",
        keyword="business",
        tags={"business", "rope"},
    ),
}


GENTLE_NAMES = ["Mara", "Tobin", "Anya", "Pip", "Jory", "Lina", "Nell", "Owen"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A plan is risky in a place if that place is windy and the plan is a business plan.
risky(P, Pl) :- place(Pl), windy(Pl), plan(P), business_plan(P).

% A plan is safe if it has a matching safer method.
safe(P) :- plan(P), has_fix(P).

% A story is valid when the place and plan are both defined, the plan is risky,
% and there is a safe fix so the ending can be happy.
valid(Pl, P) :- risky(P, Pl), safe(P).

% A cheerful folk-tale story requires a helper.
valid_story(Pl, P, H) :- valid(Pl, P), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.windy:
            lines.append(asp.fact("windy", pid))
        if p.afford_business:
            lines.append(asp.fact("business_place", pid))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("business_plan", plan_id))
        lines.append(asp.fact("has_fix", plan_id))
    lines.append(asp.fact("helper", "true"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        if not place.afford_business:
            continue
        for plan_id, plan in PLANS.items():
            if place.windy and plan.keyword == "business":
                combos.append((place_id, plan_id))
    return combos


def explain_rejection(place_id: str, plan_id: str) -> str:
    place = PLACES[place_id]
    plan = PLANS[plan_id]
    if not place.windy:
        return "(No story: this place is too calm for the cliffside trouble that makes the folk tale turn.)"
    return (
        f"(No story: {plan.name} would be ruined by the wind at {place.name}, "
        f"and there is no safe way to start the business there.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def safe_fix(plan: Plan) -> str:
    return plan.safer


def tell_story(world: World, hero: Entity, helper: Entity, plan: Plan) -> None:
    place = world.place.name

    hero.set_meme("hope", 1)
    world.say(
        f"Long ago, at {place}, there lived a little tramp named {hero.name}. "
        f"{hero.name} had a soft hat, a brave heart, and a dream of starting {plan.name}."
    )
    world.say(
        f"{hero.name} wanted to {plan.what}, because even a tramp can wish for a proper business and a fair coin."
    )

    world.para()
    hero.bump_meme("worry", 1)
    hero.bump_meter("wind", 1)
    world.say(
        f"But the cliff wind blew hard. {plan.risky.capitalize()}."
    )
    world.say(
        f"{hero.name} looked at the shaking cloth and felt worry in {hero.name.lower()}'s chest."
    )

    helper.bump_meme("trust", 1)
    world.say(
        f"Then {helper.name}, a kind neighbor, came walking by with a basket and a smile."
    )
    world.say(
        f"{helper.name} said, \"We can keep your business, but we must do it the clever way.\""
    )

    world.para()
    hero.bump_meme("pride", 1)
    hero.bump_meme("gratitude", 1)
    hero.set_meter("safety", 1)
    world.say(
        f"Together they chose to {safe_fix(plan)}."
    )
    world.say(
        f"So {hero.name} set up {plan.name} in a safe spot, and the cliff wind could not spoil it."
    )
    world.say(
        f"At last, {hero.name} sold enough to earn coins, and {helper.name} left with a warm smile."
    )

    world.para()
    world.say(
        f"By sunset, the little tramp had become a proud shopkeeper, and the cliff village had a new happy business."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        plan=plan,
        place_id=next(k for k, v in PLACES.items() if v is world.place),
        resolved=True,
    )


def generate_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    plan = PLANS[params.plan]
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type="tramp", name=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="villager", name=params.helper_name))
    world.add(Entity(id="plan", kind="thing", type="business", name=plan.name))
    tell_story(world, hero, helper, plan)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    plan: Plan = f["plan"]  # type: ignore[assignment]
    place_id = f["place_id"]
    place = PLACES[place_id].name
    return [
        f'Write a folk tale for a small child about a tramp, a cliff, and a business at {place}.',
        f"Tell a happy-ending story where {hero.name} the tramp tries to start {plan.name} and a kind helper helps.",
        f'Write a gentle story that includes the words "cliff", "tramp", and "business" and ends well.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    plan: Plan = f["plan"]  # type: ignore[assignment]
    place_id = f["place_id"]
    place = PLACES[place_id].name
    return [
        QAItem(
            question=f"Who was the tramp in the story?",
            answer=f"The tramp was {hero.name}, who lived by the cliff and wanted a better life.",
        ),
        QAItem(
            question=f"What kind of business did {hero.name} want to start?",
            answer=f"{hero.name} wanted to start {plan.name} so {hero.name.lower()} could {plan.what}.",
        ),
        QAItem(
            question=f"Why did {hero.name} need help at {place}?",
            answer=f"{plan.risky.capitalize()}, so {hero.name} needed a clever helper to keep the business safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {hero.name} used {plan.name}, earned coins, and became proud and hopeful.",
        ),
        QAItem(
            question=f"Who helped the tramp?",
            answer=f"{helper.name} helped by suggesting the safer way to set up the business.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cliff?",
            answer="A cliff is a very steep high rock or edge of land. It can be windy and dangerous near the top.",
        ),
        QAItem(
            question="What is a business?",
            answer="A business is a way of making or earning money by selling something or helping people.",
        ),
        QAItem(
            question="What is a tramp?",
            answer="A tramp is a person who travels from place to place, often with very few belongings.",
        ),
        QAItem(
            question="Why do people like happy endings?",
            answer="People like happy endings because they show that problems can be solved and things can turn out well.",
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
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cliff business tramp folk tale world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.place and args.plan:
        if (args.place, args.plan) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.plan))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.plan is None or c[1] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, plan = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(GENTLE_NAMES)
    helper_name = args.helper or rng.choice([n for n in GENTLE_NAMES if n != hero_name])
    return StoryParams(place=place, plan=plan, hero_name=hero_name, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, plan) combos ({len(stories)} with helper):\n")
        for place, plan in triples:
            helpers = sorted(g for (pl, pn, g) in stories if (pl, pn) == (place, plan))
            print(f"  {place:14} {plan:10}  [{', '.join(helpers)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, plan in sorted(valid_combos()):
            params = StoryParams(place=place, plan=plan, hero_name="Mara", helper_name="Nell")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.hero_name}: {p.plan} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
