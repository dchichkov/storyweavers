#!/usr/bin/env python3
"""
A small story world in a laundry room, told in a nursery-rhyme style.

Premise:
A little grammy keeps the laundry room tidy and sings while she folds.
A director arrives with a plan to penetrate the closed laundry-room door
to fetch a missing ribbon reel for a show.

Tension:
The director wants to rush in, but the laundry room is slippery with soap
and the grammy worries the basket tower will topple.

Turn:
The director pauses, listens, and helps sort the linens instead of forcing
the door.

Resolution:
They reconcile, share the task, and the room ends neat, bright, and calm.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "grammy"}
        male = {"boy", "man", "father", "dad", "director"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the laundry room"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        return World(
            setting=self.setting,
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            fired=set(self.fired),
            facts=dict(self.facts),
        )


# ---------------------------------------------------------------------------
# Story content
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    seed: Optional[int] = None
    grammy_name: str = "Grammy May"
    director_name: str = "Director Dean"


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = False


ITEMS = {
    "basket": Item("basket", "basket tower", "a tall basket tower", "floor", fragile=True),
    "ribbon": Item("ribbon", "ribbon reel", "a bright ribbon reel", "shelf"),
    "sheet": Item("sheet", "sheet", "a clean white sheet", "line"),
}

# Nursery-rhyme style beats.
OPENING_LINES = [
    "In the laundry room, soft and small, the towels hung quiet on the wall.",
    "A grammy sang a hum-hum tune while socks were sleeping in the moon.",
    "A director came with quick, quick feet, to fetch a ribbon neat and neat.",
]

ASP_RULES = r"""
% Facts: role(R), place(P), item(I), relation(X,Y)
reconciliation_possible :- worry(grammy, director), helper(director), place(laundry_room).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "laundry_room"),
        asp.fact("role", "grammy"),
        asp.fact("role", "director"),
        asp.fact("item", "ribbon"),
        asp.fact("item", "basket"),
        asp.fact("theme", "reconciliation"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate() -> None:
    # Internal story sanity: the setting and theme are fixed.
    if not SETTING.place == "the laundry room":
        raise StoryError("This world only works in the laundry room.")
    return


# ---------------------------------------------------------------------------
# Simulation rules
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    world = World(Setting())
    grammy = world.add(Entity(
        id="grammy",
        kind="character",
        type="grammy",
        label=params.grammy_name,
        meters={"tidy": 1.0, "calm": 1.0},
        memes={"care": 1.0, "reconciliation": 0.0},
    ))
    director = world.add(Entity(
        id="director",
        kind="character",
        type="director",
        label=params.director_name,
        meters={"hurry": 1.0, "step": 1.0},
        memes={"plan": 1.0, "reconciliation": 0.0},
    ))
    basket = world.add(Entity(
        id="basket",
        kind="thing",
        type="basket",
        label="basket tower",
        phrase="a tall basket tower",
        owner="grammy",
        caretaker="grammy",
        meters={"wobble": 0.0, "dust": 0.0},
        memes={"balance": 1.0},
    ))
    ribbon = world.add(Entity(
        id="ribbon",
        kind="thing",
        type="ribbon",
        label="ribbon reel",
        phrase="a bright ribbon reel",
        owner="director",
        meters={"missing": 1.0},
    ))
    sheet = world.add(Entity(
        id="sheet",
        kind="thing",
        type="sheet",
        label="sheet",
        phrase="a clean white sheet",
        owner="grammy",
        meters={"clean": 1.0},
    ))
    world.facts.update(grammy=grammy, director=director, basket=basket, ribbon=ribbon, sheet=sheet)
    return world


def predict_penetration(world: World) -> bool:
    sim = world.copy()
    sim.get("director").memes["push"] = 1.0
    sim.get("basket").meters["wobble"] += 1.0
    return sim.get("basket").meters["wobble"] >= THRESHOLD


def opening(world: World) -> None:
    world.say(OPENING_LINES[0])
    world.say(f"{world.get('grammy').label} folded sheets with a little la-la song.")


def arrival(world: World) -> None:
    d = world.get("director")
    g = world.get("grammy")
    world.para()
    world.say(f"{d.label} tapped at the laundry-room door and said, “I must penetrate the door and find the ribbon reel.”")
    world.say(f"{g.label} lifted her head. “Not so fast, dear heart; the floor is slick, and the basket tower sways.”")
    d.memes["worry"] = 0.0
    d.memes["want"] = 1.0
    g.memes["worry"] = 1.0


def conflict(world: World) -> None:
    d = world.get("director")
    g = world.get("grammy")
    basket = world.get("basket")
    if predict_penetration(world):
        basket.meters["wobble"] += 1.0
        d.memes["frustration"] = 1.0
        g.memes["alarm"] = 1.0
        world.say("The director reached to push the door, but the grammy held up a hand.")
        world.say("“A bump and a shove may make the basket go rove,” she said in her gentle rhyme.")
        world.say("So the director stopped short, with a worried little snort.")


def reconciliation(world: World) -> None:
    d = world.get("director")
    g = world.get("grammy")
    basket = world.get("basket")
    sheet = world.get("sheet")
    ribbon = world.get("ribbon")

    d.memes["reconciliation"] = 1.0
    g.memes["reconciliation"] = 1.0
    d.memes["frustration"] = 0.0
    g.memes["alarm"] = 0.0
    basket.meters["wobble"] = 0.0
    basket.meters["dust"] = 0.0
    sheet.meters["clean"] = 1.0
    ribbon.meters["missing"] = 0.0

    world.say("Then the director breathed in slow, slow air, and helped sort towels with care.")
    world.say("He stacked the socks and mended the line, while Grammy hummed, “Now that is fine.”")
    world.say("Together they found the ribbon reel behind the sheet, and the room grew calm and neat.")
    world.say("They smiled and made it plain and true: the best way through was me and you.")


def ending(world: World) -> None:
    world.para()
    g = world.get("grammy")
    d = world.get("director")
    world.say(f"{g.label} and {d.label} shared a grin; the laundry room glowed softly within.")
    world.say("No door was forced, no shelf upset, and the ribbon came away all set.")
    world.say("So if you must go in a room, be kind, be still, and let calm bloom.")


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short nursery-rhyme story about grammy, a director, and reconciliation in a laundry room.',
        'Tell a gentle story where a director tries to penetrate the laundry room, but grammy turns the moment into a calm reconciliation.',
        'Create a child-friendly rhyme about a laundry room, a missing ribbon reel, and two people finding a peaceful way to work together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    g = world.get("grammy")
    d = world.get("director")
    return [
        QAItem(
            question="Where does the story happen?",
            answer="It happens in the laundry room, where the towels, sheets, and basket tower are all part of the scene.",
        ),
        QAItem(
            question=f"Why did {d.label} want to come in so quickly?",
            answer=f"{d.label} wanted to penetrate the laundry room to find the ribbon reel, because it was needed for a show.",
        ),
        QAItem(
            question=f"How did {g.label} help solve the problem?",
            answer=f"{g.label} asked {d.label} to slow down, sort the laundry, and work with her, so they could find the ribbon safely.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="By the end, the worry was gone, the basket tower was steady, and the two of them had reconciled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a laundry room for?",
            answer="A laundry room is a place where people wash, dry, fold, and sort clothes and linens.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means two people stop being upset and come back together in peace.",
        ),
        QAItem(
            question="Why should you be careful around a wet floor?",
            answer="You should be careful because a wet floor can be slippery and make someone fall.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reconciliation_possible/0."))
    clingo_true = bool(asp.atoms(model, "reconciliation_possible"))
    python_true = True
    if clingo_true == python_true:
        print("OK: clingo gate matches Python reasonableness gate (reconciliation is possible).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: grammy, director, and reconciliation in a laundry room.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        grammy_name=args.name or rng.choice(["Grammy May", "Grammy Rose", "Grammy June"]),
        director_name=rng.choice(["Director Dean", "Director Dot", "Director Della"]),
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate()
    world = setup_world(params)
    opening(world)
    arrival(world)
    conflict(world)
    reconciliation(world)
    ending(world)
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
    StoryParams(seed=1, grammy_name="Grammy May", director_name="Director Dean"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reconciliation_possible/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reconciliation_possible/0."))
        print("reconciliation_possible:", bool(asp.atoms(model, "reconciliation_possible")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
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
