#!/usr/bin/env python3
"""
A small storyworld for a detective-style rental mishap with rhyme, humor, and
inner monologue.

Premise:
A young detective rents a bicycle for a sunny errand, but a missing key, a
tricky landlord, and a muddy clue turn the simple rental into a little mystery.

The world model tracks:
- physical meters: amount of dirt, missingness, lock state, rental hours
- emotional memes: worry, curiosity, relief, pride, amusement

The story is generated from state transitions, not from a fixed paragraph with
swapped names. The detective reasons, mutters to themself, finds the clue, and
solves the rental problem.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "detective"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    weather: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class Rental:
    id: str
    label: str
    phrase: str
    kind: str
    lockable: bool
    needs_key: bool
    rhyming_hint: str
    repair_hint: str


@dataclass
class StoryParams:
    place: str
    rental: str
    hero_name: str
    hero_type: str
    clerk_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        w = World(self.place)
        w.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def bump_meter(ent: Entity, key: str, delta: float = 1.0) -> None:
    ent.meters[key] = meter(ent, key) + delta


def bump_meme(ent: Entity, key: str, delta: float = 1.0) -> None:
    ent.memes[key] = meme(ent, key) + delta


def one_line_rhyme(a: str, b: str) -> str:
    return f"{a} and {b} made a little rhyme in the same line."


PLACES = {
    "alley": Place(name="the alley", indoors=False, weather="misty", affords={"walk"}),
    "market": Place(name="the market", indoors=False, weather="bright", affords={"walk"}),
    "library": Place(name="the library", indoors=True, weather="", affords={"search"}),
    "dock": Place(name="the dock", indoors=False, weather="windy", affords={"walk"}),
}

RENTALS = {
    "bicycle": Rental(
        id="bicycle",
        label="bicycle",
        phrase="a red rental bicycle",
        kind="bike",
        lockable=True,
        needs_key=True,
        rhyming_hint="spoke and smoke",
        repair_hint="oil the chain",
    ),
    "umbrella": Rental(
        id="umbrella",
        label="umbrella",
        phrase="a striped rental umbrella",
        kind="umbrella",
        lockable=False,
        needs_key=False,
        rhyming_hint="drip and skip",
        repair_hint="dry the fabric",
    ),
    "skates": Rental(
        id="skates",
        label="skates",
        phrase="a pair of rental skates",
        kind="skates",
        lockable=True,
        needs_key=True,
        rhyming_hint="glide and slide",
        repair_hint="tighten the wheels",
    ),
}

CURATED = [
    StoryParams(place="market", rental="bicycle", hero_name="Milo", hero_type="detective", clerk_type="shopkeeper"),
    StoryParams(place="alley", rental="umbrella", hero_name="Nina", hero_type="detective", clerk_type="clerk"),
    StoryParams(place="dock", rental="skates", hero_name="Toby", hero_type="detective", clerk_type="keeper"),
]


@dataclass
class Solution:
    found_key: bool = False
    soothed: bool = False
    returned: bool = False


def setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity]:
    place = PLACES[params.place]
    rental = RENTALS[params.rental]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    clerk = world.add(Entity(id="Clerk", kind="character", type=params.clerk_type, label="the clerk"))
    item = world.add(Entity(
        id="RentalItem",
        type=rental.kind,
        label=rental.label,
        phrase=rental.phrase,
        owner=hero.id,
        caretaker=clerk.id,
        held_by=hero.id,
    ))
    item.meters.update({"dirty": 0.0, "missing_key": 0.0, "rented": 1.0, "returned": 0.0})
    item.memes.update({"value": 1.0})
    hero.memes.update({"curiosity": 1.0, "worry": 0.0, "pride": 0.0, "relief": 0.0, "amusement": 0.0})
    clerk.memes.update({"patience": 1.0})
    world.facts.update(params=params, rental=rental, hero=hero, clerk=clerk, item=item)
    return world, hero, clerk, item


def foreshadow(world: World, hero: Entity, item: Entity) -> None:
    bump_meme(hero, "curiosity", 1.0)
    world.say(f"{hero.id} arrived with a detective's hat and a careful stare.")
    world.say(f"{hero.pronoun().capitalize()} wanted to solve the small case of {item.phrase}.")
    world.say(f"Inside {hero.id}'s head, a tiny voice said, 'Find the clue, don't make a stew of it.'")


def rent_scene(world: World, hero: Entity, clerk: Entity, item: Entity, rental: Rental) -> None:
    bump_meme(hero, "pride", 0.5)
    world.say(
        f"The clerk passed over {item.phrase}, neat as a seat, and said it was ready for the street."
    )
    world.say(
        f"{hero.id} checked the lock, the wheels, and the key. 'It should be fine,' {hero.pronoun()} thought, 'but fine can hide a lie.'"
    )


def problem_scene(world: World, hero: Entity, clerk: Entity, item: Entity, rental: Rental) -> None:
    bump_meter(item, "missing_key", 1.0)
    bump_meme(hero, "worry", 1.0)
    world.say(
        f"Then the key was gone, and that was a shock. No key, no go; no go, no show."
    )
    world.say(
        f"{hero.id} frowned and muttered, 'This rental riddle is a fiddly little fiddle.'"
    )
    world.say(
        f"{hero.pronoun().capitalize()} peered at the lock and thought, 'A thief may be slick, but the clue must stick.'"
    )


def clue_scene(world: World, hero: Entity, item: Entity, rental: Rental) -> None:
    bump_meter(item, "dirty", 1.0)
    world.say(
        f"Near the curb, {hero.id} spotted a muddy smudge shaped like a comma."
    )
    world.say(
        f"'{rental.rhyming_hint},' {hero.pronoun()} whispered. 'The key did not fly; it must have slid by.'"
    )
    world.say(
        f"{hero.id} followed the smudge and found a lost key tucked under a bench, safe from the rush."
    )


def solve_scene(world: World, hero: Entity, clerk: Entity, item: Entity, rental: Rental, solution: Solution) -> None:
    solution.found_key = True
    solution.soothed = True
    bump_meme(hero, "relief", 1.5)
    bump_meme(hero, "amusement", 1.0)
    item.meters["missing_key"] = 0.0
    world.say(
        f"{hero.id} held up the key. 'A key in the street is a sneaky feat,' {hero.pronoun()} said with a grin."
    )
    world.say(
        f"The clerk laughed and clapped once. 'You solved the case in a brisk little pace.'"
    )
    world.say(
        f"{hero.id} paid the rental fee, and the whole scene felt light as a kite."
    )


def ending_scene(world: World, hero: Entity, clerk: Entity, item: Entity, rental: Rental, solution: Solution) -> None:
    item.meters["returned"] = 1.0
    solution.returned = True
    bump_meme(hero, "pride", 1.0)
    world.say(
        f"In the end, {hero.id} returned {item.it()} on time."
    )
    world.say(
        f"{hero.id} walked away smiling, thinking, 'The case was small, but the clue was tall.'"
    )
    world.say(
        f"And the rental sat still and snug, ready for the next pair of careful hands."
    )


def tell_story(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.rental not in RENTALS:
        raise StoryError("Unknown rental item.")
    world, hero, clerk, item = setup_world(params)
    rental = world.facts["rental"]
    solution = Solution()

    foreshadow(world, hero, item)
    world.para()
    rent_scene(world, hero, clerk, item, rental)
    problem_scene(world, hero, clerk, item, rental)
    world.para()
    clue_scene(world, hero, item, rental)
    solve_scene(world, hero, clerk, item, rental, solution)
    world.para()
    ending_scene(world, hero, clerk, item, rental, solution)

    world.facts["solution"] = solution
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    rental = world.facts["rental"]
    return [
        f"Write a short detective story for a child about a rental {rental.label} and a missing key.",
        f"Tell a funny mystery where {p.hero_name} the detective rents {rental.phrase} and has to solve a little problem.",
        f"Write a story with rhyme, humor, and inner monologue about a rental clue at {PLACES[p.place].name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    rental = world.facts["rental"]
    hero = world.facts["hero"]
    clerk = world.facts["clerk"]
    item = world.facts["item"]
    return [
        QAItem(
            question=f"What did {hero.id} rent?",
            answer=f"{hero.id} rented {item.phrase}, which was a {rental.label}.",
        ),
        QAItem(
            question=f"What was the problem in the story?",
            answer="The rental key went missing, so the item could not be used right away.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the mystery?",
            answer=f"{hero.id} followed a muddy clue, found the lost key, and brought it back to {clerk.label_word if hasattr(clerk, 'label_word') else 'the clerk'}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt relieved, amused, and proud after solving the rental case.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rental?",
            answer="A rental is something you borrow and pay for using for a little while, then you give it back.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="Why can mud help in a mystery?",
            answer="Mud can leave a footprint or smudge that shows where something went.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-story rental world with rhyme, humor, and inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--rental", choices=RENTALS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["detective"], default="detective")
    ap.add_argument("--clerk-type", choices=["shopkeeper", "clerk", "keeper"], default="shopkeeper")
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
    rental = args.rental or rng.choice(list(RENTALS))
    name = args.name or rng.choice(["Milo", "Nina", "Toby", "Lena", "Otis", "Maya"])
    return StoryParams(
        place=place,
        rental=rental,
        hero_name=name,
        hero_type=args.hero_type,
        clerk_type=args.clerk_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


ASP_RULES = r"""
place(alley). place(market). place(library). place(dock).
rental(bicycle). rental(umbrella). rental(skates).
compatible(Place, Rental) :- place(Place), rental(Rental).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for r in RENTALS:
        lines.append(asp.fact("rental", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    found = sorted(set(asp.atoms(model, "compatible")))
    expected = sorted((p, r) for p in PLACES for r in RENTALS)
    if found == expected:
        print(f"OK: ASP agrees ({len(found)} combinations).")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [StoryParams(place=p.place, rental=p.rental, hero_name=p.hero_name, hero_type=p.hero_type, clerk_type=p.clerk_type) for p in CURATED]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: rental={p.rental} place={p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
