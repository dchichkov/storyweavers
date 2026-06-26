#!/usr/bin/env python3
"""
A standalone storyworld for a small Suspense / Space Adventure domain.

Seed imagination:
- A tiny crew flies to a drifting station.
- They need to carry a bag of money to buy a part.
- A cargo ring has a narrow diameter, so only the right crate fits.
- A loaf of rye becomes the key clue in a tense, child-friendly rescue.

The world is intentionally small and constraint-driven:
- physical meters track things like distance, diameter, and cargo fit
- emotional memes track worry, relief, trust, and suspense
- the story is generated from the simulated state, not a frozen template
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

# -----------------------------------------------------------------------------
# World constants
# -----------------------------------------------------------------------------
THRESHOLD = 1.0

CREW_NAMES = ["Mina", "Jori", "Tess", "Luca", "Nia", "Pip", "Rae", "Soren"]
SHIP_NAMES = ["Comet Kite", "Star Moth", "Little Orbit", "Moon Finch"]
ROLE_NAMES = ["captain", "pilot", "engineer", "scanner"]
LOCATIONS = ["cargo bay", "airlock", "orbital market", "drift station", "quiet corridor"]
OBJECT_NAMES = ["tool crate", "money pouch", "rye loaf", "seal ring", "spare coil"]

# -----------------------------------------------------------------------------
# Data model
# -----------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False
    protective: bool = False
    fits_diameter: Optional[float] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    dock: str
    corridor_diameter: float
    cargo_hold_diameter: float
    station_name: str
    facts: dict = field(default_factory=dict)


@dataclass
class Puzzle:
    id: str
    label: str
    phrase: str
    danger: str
    clue: str
    requires_diameter_under: float
    tags: set[str] = field(default_factory=set)


@dataclass
class MoneyItem:
    id: str
    label: str
    phrase: str
    amount: int
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class FoodItem:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    ship: str
    puzzle: str
    money: int
    rye: bool
    crew_name: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship):
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.ship)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------
SHIPS = {
    "comet_kite": Ship("Comet Kite", "Dock Nine", 1.2, 2.0, "drift station"),
    "star_moth": Ship("Star Moth", "Ring Gate", 0.9, 1.6, "orbital market"),
    "little_orbit": Ship("Little Orbit", "Blue Spur", 1.0, 1.8, "drift station"),
}

PUZZLES = {
    "seal_ring": Puzzle(
        id="seal_ring",
        label="seal ring",
        phrase="a narrow seal ring for the airlock",
        danger="the air could leak out",
        clue="the ring must slide through a tight opening",
        requires_diameter_under=1.05,
        tags={"space", "diameter", "suspense"},
    ),
    "cargo_gate": Puzzle(
        id="cargo_gate",
        label="cargo gate",
        phrase="a cargo gate with a tiny opening",
        danger="the part might not fit",
        clue="the opening is smaller than the crate",
        requires_diameter_under=1.15,
        tags={"space", "diameter", "suspense"},
    ),
}

MONEY = {
    5: MoneyItem("small_cash", "small money pouch", "a small pouch of money", 5, tags={"money"}),
    12: MoneyItem("mid_cash", "money pouch", "a pouch of money", 12, tags={"money"}),
    20: MoneyItem("big_cash", "full money pouch", "a full pouch of money", 20, tags={"money"}),
}

RYE = FoodItem("rye_loaf", "rye loaf", "a loaf of rye bread", tags={"rye", "food"})

# -----------------------------------------------------------------------------
# Story logic
# -----------------------------------------------------------------------------
def ship_for_story(ship_id: str) -> Ship:
    return SHIPS[ship_id]


def puzzle_needs_fit(puzzle: Puzzle, diameter: float) -> bool:
    return diameter <= puzzle.requires_diameter_under


def resolve_reasonable(ship: Ship, puzzle: Puzzle) -> bool:
    return puzzle.requires_diameter_under >= 0.9 and ship.cargo_hold_diameter >= puzzle.requires_diameter_under


def predict_problem(world: World, crew: Entity, puzzle: Puzzle, money: MoneyItem, rye: bool) -> dict:
    sim = world.copy()
    crew2 = sim.get(crew.id)
    crew2.memes["worry"] = crew2.memes.get("worry", 0.0) + 1
    crew2.meters["distance"] = crew2.meters.get("distance", 0.0) + 1
    fit = puzzle_needs_fit(puzzle, sim.ship.cargo_hold_diameter)
    money_safe = money.amount >= 10
    rye_clue = rye
    return {"fit": fit, "money_safe": money_safe, "rye_clue": rye_clue}


def intro(world: World, crew: Entity) -> None:
    world.say(
        f"{crew.id} was a young {crew.type} who kept one eye on the stars and one eye on every little switch."
    )


def setup(world: World, crew: Entity, puzzle: Puzzle, money: MoneyItem, rye: FoodItem, role: str) -> None:
    ship = world.ship
    world.say(
        f"{crew.id} served as the {role} aboard the {ship.name}, where every tool had a place and every sound mattered."
    )
    world.say(
        f"One day, the crew needed {money.phrase} to buy {puzzle.phrase} at the {ship.station_name}."
    )
    if rye:
        world.say(
            f"They also packed {rye.phrase} for the trip, because a long watch is easier with a warm snack."
        )


def tension(world: World, crew: Entity, puzzle: Puzzle, money: MoneyItem) -> None:
    crew.memes["suspense"] = crew.memes.get("suspense", 0.0) + 1
    world.say(
        f"When they reached the {world.ship.dock}, {crew.id} noticed the problem right away: {puzzle.clue}."
    )
    world.say(
        f"If they chose the wrong route, {puzzle.danger}."
    )
    world.say(
        f"{crew.id} clutched the money pouch a little tighter and listened to the ship hum in the dark."
    )


def clue_scene(world: World, crew: Entity, puzzle: Puzzle, rye: FoodItem, money: MoneyItem) -> None:
    crew.memes["worry"] = crew.memes.get("worry", 0.0) + 1
    world.say(
        f"Then {crew.id} spotted the rye loaf near the console, and that tiny clue changed everything."
    )
    world.say(
        f"The loaf had fallen from the crate, which meant the crate had not moved far and the missing part was still close by."
    )
    world.say(
        f"That made the narrow opening less scary, because the crew could search the right place first instead of guessing."
    )


def rescue_turn(world: World, crew: Entity, puzzle: Puzzle, money: MoneyItem, rye: FoodItem) -> None:
    crew.memes["hope"] = crew.memes.get("hope", 0.0) + 1
    world.say(
        f"{crew.id} used the money to open the service panel and ask the station helper for the exact seal."
    )
    world.say(
        f"With the correct part, the fit was just right for the tiny diameter, and the air stayed safely inside."
    )
    world.say(
        f"The rye loaf made the whole search feel clever instead of rushed, as if the station itself had left a trail of breadcrumbs among the stars."
    )


def ending(world: World, crew: Entity, puzzle: Puzzle) -> None:
    crew.memes["worry"] = max(0.0, crew.memes.get("worry", 0.0) - 1)
    crew.memes["relief"] = crew.memes.get("relief", 0.0) + 1
    world.say(
        f"In the end, {crew.id} smiled at the quiet hatch and the steady ship lights."
    )
    world.say(
        f"The little crew had kept the money safe, solved the diameter problem, and brought the {puzzle.label} home before the stars blinked out."
    )


def build_world(params: StoryParams) -> World:
    ship = ship_for_story(params.ship)
    world = World(ship)
    crew = world.add(Entity(id=params.crew_name, kind="character", type="girl" if params.crew_name in {"Mina", "Tess", "Nia", "Rae"} else "boy"))
    puzzle = PUZZLES[params.puzzle]
    money = MONEY[params.money]
    rye = RYE if params.rye else None

    world.facts.update(ship=ship, crew=crew, puzzle=puzzle, money=money, rye=rye, role=params.role)

    crew.meters["distance"] = 0.0
    crew.memes["suspense"] = 0.0

    intro(world, crew)
    setup(world, crew, puzzle, money, rye or RYE, params.role)
    world.para()
    tension(world, crew, puzzle, money)
    clue_scene(world, crew, puzzle, rye or RYE, money)
    world.para()
    rescue_turn(world, crew, puzzle, money, rye or RYE)
    ending(world, crew, puzzle)
    return world


# -----------------------------------------------------------------------------
# QA
# -----------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    crew = f["crew"]
    puzzle = f["puzzle"]
    ship = f["ship"]
    return [
        f'Write a short Suspense story for a child about a crew member named {crew.id} on the ship {ship.name}.',
        f"Tell a space adventure where {crew.id} must solve a tiny diameter problem before buying {puzzle.phrase}.",
        f'Write a gentle suspense story that includes money, rye, and a narrow space-station opening.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    crew = f["crew"]
    puzzle = f["puzzle"]
    ship = f["ship"]
    money = f["money"]
    rye = f["rye"]
    return [
        QAItem(
            question=f"Who worried about the problem on the ship {ship.name}?",
            answer=f"{crew.id} worried, because the crew needed the right part and the opening was very narrow.",
        ),
        QAItem(
            question=f"What was the money for in the story?",
            answer=f"The money was used to buy {puzzle.phrase} at the station.",
        ),
        QAItem(
            question=f"Why did the rye loaf matter?",
            answer=f"The rye loaf was a clue that helped the crew search the right place first.",
        ),
        QAItem(
            question=f"What solved the problem with the diameter?",
            answer=f"Using the correct part solved the diameter problem and kept the air safely inside.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is diameter?",
            answer="Diameter is the distance across a round object through the middle.",
        ),
        QAItem(
            question="What is money used for?",
            answer="Money is used to pay for things you need or want to buy.",
        ),
        QAItem(
            question="What is rye?",
            answer="Rye is a kind of grain that people use to make bread.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense means the story makes you wonder what will happen next and feel a little tense.",
        ),
    ]


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
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------
ASP_RULES = r"""
puzzle_fit(P) :- puzzle(P), needs_under(P, D), ship_hold(H), H >= D.
safe_story(S, P, M) :- ship(S), puzzle(P), money(M), puzzle_fit(P).
uses_rye(S) :- story_has_rye(S).
relevant(S, P, M) :- safe_story(S, P, M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, ship in SHIPS.items():
        lines.append(asp.fact("ship", sid))
        lines.append(asp.fact("ship_hold", ship.cargo_hold_diameter))
    for pid, p in PUZZLES.items():
        lines.append(asp.fact("puzzle", pid))
        lines.append(asp.fact("needs_under", pid, p.requires_diameter_under))
    for m in MONEY:
        lines.append(asp.fact("money", m))
    lines.append(asp.fact("story_has_rye", "yes"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show relevant/3."))
    return sorted(set(asp.atoms(model, "relevant")))


def python_valid() -> list[tuple]:
    vals = []
    for sid, ship in SHIPS.items():
        for pid, p in PUZZLES.items():
            for m in MONEY:
                if resolve_reasonable(ship, p):
                    vals.append((sid, pid, m))
    return sorted(set(vals))


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(python_valid())
    if a == b:
        print(f"OK: ASP parity holds for {len(a)} combinations.")
        return 0
    print("Mismatch between ASP and Python:")
    print("only ASP:", sorted(a - b))
    print("only Python:", sorted(b - a))
    return 1


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suspense / Space Adventure storyworld.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--money", type=int, choices=sorted(MONEY))
    ap.add_argument("--rye", action="store_true", help="include rye in the story")
    ap.add_argument("--crew-name", choices=CREW_NAMES)
    ap.add_argument("--role", choices=ROLE_NAMES)
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
    ship = args.ship or rng.choice(list(SHIPS))
    puzzle = args.puzzle or rng.choice(list(PUZZLES))
    money = args.money or rng.choice(list(MONEY))
    crew_name = args.crew_name or rng.choice(CREW_NAMES)
    role = args.role or rng.choice(ROLE_NAMES)
    rye = bool(args.rye) or rng.random() < 0.7

    if not resolve_reasonable(SHIPS[ship], PUZZLES[puzzle]):
        raise StoryError("That ship and puzzle do not make a reasonable diameter problem.")
    return StoryParams(ship=ship, puzzle=puzzle, money=money, rye=rye, crew_name=crew_name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  ship={world.ship.name} cargo_hold_diameter={world.ship.cargo_hold_diameter}")
    lines.append(f"  facts={list(world.facts.keys())}")
    return "\n".join(lines)


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
        print(asp_program("#show relevant/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} compatible stories:")
        for sid, pid, m in vals:
            print(f"  {sid:12} {pid:12} money={m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(ship="comet_kite", puzzle="seal_ring", money=12, rye=True, crew_name="Mina", role="engineer"),
            StoryParams(ship="star_moth", puzzle="cargo_gate", money=20, rye=True, crew_name="Jori", role="scanner"),
            StoryParams(ship="little_orbit", puzzle="seal_ring", money=5, rye=True, crew_name="Tess", role="pilot"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
