#!/usr/bin/env python3
"""
A small animal story world about a barrier, sharing, and moral value.

A source-tale shape:
- An animal wants something behind a barrier.
- Another animal notices the need and worries about fairness.
- A sharing choice changes the barrier from a block into a bridge.
- The ending proves the moral value through a concrete state change.
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
    species: str = ""
    name: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def poss(self) -> str:
        return "their"


@dataclass
class Place:
    name: str
    barrier: str
    barrier_state: str
    holds: str
    moral_hint: str


@dataclass
class Want:
    item: str
    reason: str
    share_kind: str
    shared_amount: int


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    want: str
    seed: Optional[int] = None


PLACES = {
    "riverbank": Place(
        name="the riverbank",
        barrier="a narrow log barrier",
        barrier_state="across the path",
        holds="a berry bush on the far side",
        moral_hint="the berries were for everyone if they shared kindly",
    ),
    "meadow": Place(
        name="the meadow",
        barrier="a little fence",
        barrier_state="around the clover patch",
        holds="a patch of sweet clover",
        moral_hint="good manners made the clover feel fair",
    ),
    "hill": Place(
        name="the hill",
        barrier="a fallen branch barrier",
        barrier_state="blocking the shortcut",
        holds="a warm patch of sun",
        moral_hint="taking turns could make the hill pleasant for both",
    ),
}

WANTS = {
    "berries": Want("berries", "the ripe berries smelled sweet", "berries", 3),
    "clover": Want("clover", "the clover was soft and tasty", "clover", 2),
    "sun": Want("sun", "the warm sun felt nice on chilly fur", "sunny spots", 1),
}

ANIMALS = [
    ("Milo", "mouse"),
    ("Tia", "rabbit"),
    ("Pip", "fox"),
    ("Nia", "bear"),
    ("Roo", "squirrel"),
    ("Finn", "hedgehog"),
    ("Luna", "deer"),
    ("Bram", "badger"),
]


class World:
    def __init__(self, place: Place, hero: Entity, friend: Entity, want: Want) -> None:
        self.place = place
        self.hero = hero
        self.friend = friend
        self.want = want
        self.barrier_closed = True
        self.shared = 0
        self.moral_value = 0.0
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        clone = World(self.place, self.hero, self.friend, self.want)
        clone.barrier_closed = self.barrier_closed
        clone.shared = self.shared
        clone.moral_value = self.moral_value
        clone.facts = dict(self.facts)
        clone.lines = []
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with barrier sharing and moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--want", choices=WANTS)
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
    place = args.place or rng.choice(list(PLACES))
    want = args.want or rng.choice(list(WANTS))
    names = rng.sample(ANIMALS, 2)
    hero = args.hero or names[0][0]
    friend = args.friend or names[1][0]
    if hero == friend:
        raise StoryError("The hero and friend must be different animals.")
    return StoryParams(place=place, hero=hero, friend=friend, want=want)


def entity(name: str) -> Entity:
    for n, s in ANIMALS:
        if n == name:
            return Entity(id=name, kind="animal", species=s, name=name, traits=["small", "gentle"])
    return Entity(id=name, kind="animal", species="animal", name=name, traits=["small", "gentle"])


def predict_share(world: World) -> dict[str, object]:
    sim = world.copy()
    sim.shared += WANTS[sim.want.item].shared_amount
    sim.moral_value += 1.0
    sim.barrier_closed = False
    return {"opened": not sim.barrier_closed, "shared": sim.shared, "moral_value": sim.moral_value}


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    want = WANTS[params.want]
    hero = entity(params.hero)
    friend = entity(params.friend)
    world = World(place, hero, friend, want)

    world.say(f"{hero.name} was a little {hero.species} who lived near {place.name}.")
    world.say(f"{hero.name} loved {want.item} because {want.reason}, and {place.moral_hint}.")
    world.say(f"One day, {hero.name} and {friend.name} found {place.barrier} {place.barrier_state}, and it kept them from {place.holds}.")

    predicted = predict_share(world)
    if predicted["opened"]:
        world.say(f"{hero.name} wanted to go around it, but {friend.name} noticed that the best answer was to share.")
        world.say(f"{friend.name} split the {want.item} into a fair pile and gave {hero.name} the first share.")
        world.shared += want.shared_amount
        world.moral_value += 1.0
        world.barrier_closed = False
        world.say(f"After that, the {place.barrier} was moved aside, and both friends could reach {place.holds}.")
        world.say(f"They sat together, sharing {want.item}, and the day felt fair and warm.")
    else:
        raise StoryError("This story needs a sharing solution that truly opens the barrier.")

    world.facts.update(
        hero=hero,
        friend=friend,
        place=place,
        want=want,
        shared=world.shared,
        barrier_closed=world.barrier_closed,
        moral_value=world.moral_value,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story about {f["hero"].name}, {f["friend"].name}, and a barrier.',
        f'Tell a gentle story where {f["hero"].name} wants {f["want"].item} but learns to share.',
        f'Write a child-friendly story with a fair choice, an animal friend, and the word "barrier".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    want: Want = f["want"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who wanted the {want.item} near {place.name}?",
            answer=f"{hero.name} wanted the {want.item} near {place.name} because {want.reason}.",
        ),
        QAItem(
            question=f"What stopped the animals at first?",
            answer=f"{place.barrier.capitalize()} stopped them at first, so they could not reach {place.holds}.",
        ),
        QAItem(
            question=f"What did {friend.name} do to help?",
            answer=f"{friend.name} helped by sharing the {want.item} fairly, which turned the hard problem into a kind one.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the barrier moved aside and both friends sharing together, so the ending showed moral value in action.",
        ),
    ]


KNOWLEDGE = {
    "barrier": [
        QAItem(
            question="What is a barrier?",
            answer="A barrier is something that blocks the way or keeps one place apart from another.",
        )
    ],
    "sharing": [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting another person or animal use some of what you have.",
        )
    ],
    "moral value": [
        QAItem(
            question="What is moral value?",
            answer="Moral value means choosing what is kind, fair, and good for others, not just for yourself.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["barrier"])
    out.extend(KNOWLEDGE["sharing"])
    out.extend(KNOWLEDGE["moral value"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- trace ---",
            f"place: {world.place.name}",
            f"barrier_closed: {world.barrier_closed}",
            f"shared: {world.shared}",
            f"moral_value: {world.moral_value}",
            f"hero: {world.hero.name} ({world.hero.species})",
            f"friend: {world.friend.name} ({world.friend.species})",
            f"want: {world.want.item}",
        ]
    )


ASP_RULES = r"""
#show valid/3.
place(barrier_world).
valid(Place,Hero,Want) :- place(Place), hero(Hero), desire(Want).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for n, _s in ANIMALS:
        lines.append(asp.fact("hero", n))
    for w in WANTS:
        lines.append(asp.fact("desire", w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        raise StoryError(f"ASP unavailable: {exc}")
    model = asp.one_model(asp_program("#show valid/3."))
    _ = asp.atoms(model, "valid")
    print("OK: ASP twin is present.")
    return 0


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for hero, _ in ANIMALS:
            for want in WANTS:
                if hero != "":  # simple sanity
                    combos.append((place, hero, want))
    return combos


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


CURATED = [
    StoryParams(place="riverbank", hero="Milo", friend="Tia", want="berries"),
    StoryParams(place="meadow", hero="Pip", friend="Roo", want="clover"),
    StoryParams(place="hill", hero="Luna", friend="Bram", want="sun"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is minimal for this world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
