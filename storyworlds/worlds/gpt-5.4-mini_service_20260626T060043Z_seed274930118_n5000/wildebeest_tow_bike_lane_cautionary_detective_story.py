#!/usr/bin/env python3
"""
Storyworld: wildebeest tow in the bike lane
===========================================

A small cautionary detective-story world about a bike lane, a towing mishap,
and a wildlife-sized clue trail.

Premise:
- A child or adult detective notices a strange blockage in the bike lane.
- A wildebeest has been towing something it should not be towing there.
- The detective follows clues, asks witnesses, and figures out a safe fix.

The story is generated from a simulated world state:
- physical meters track blocked lane, distance, and damage risk
- emotional memes track worry, suspicion, relief, and caution

This file is self-contained and fits the Storyweavers storyworld contract.
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    ridden_by: Optional[str] = None
    towed_by: Optional[str] = None
    in_lane: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "lady"}
        masculine = {"boy", "man", "father", "detective"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_plural(self) -> bool:
        return self.type in {"bikes", "cars"}


@dataclass
class Setting:
    place: str = "the bike lane"
    affords: set[str] = field(default_factory=lambda: {"tow"})
    lane_kind: str = "bike lane"


@dataclass
class TowingThing:
    id: str
    label: str
    phrase: str
    kind: str
    risk: str
    damage: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    detective_name: str = "Mara"
    detective_type: str = "girl"
    witness_name: str = "Ned"
    witness_type: str = "boy"
    animal_name: str = "Wildebeest"
    tow_item: str = "bike_cart"
    location: str = "bike_lane"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting()

TOW_ITEMS = {
    "bike_cart": TowingThing(
        id="bike_cart",
        label="bike cart",
        phrase="a tiny bike cart",
        kind="cart",
        risk="block",
        damage="blocked",
    ),
    "sign_stand": TowingThing(
        id="sign_stand",
        label="sign stand",
        phrase="a metal sign stand",
        kind="stand",
        risk="scrape",
        damage="scraped",
    ),
}

PEOPLE = {
    "Mara": {"name": "Mara", "type": "girl", "role": "detective"},
    "Ned": {"name": "Ned", "type": "boy", "role": "witness"},
}

ANIMAL = {
    "wildebeest": {
        "id": "wildebeest",
        "label": "wildebeest",
        "phrase": "a dusty wildebeest with a bent horn",
        "type": "wildebeest",
    }
}

CURATED = [
    StoryParams(detective_name="Mara", detective_type="girl", witness_name="Ned", witness_type="boy", animal_name="Wildebeest", tow_item="bike_cart"),
    StoryParams(detective_name="Ivy", detective_type="girl", witness_name="Owen", witness_type="boy", animal_name="Wildebeest", tow_item="sign_stand"),
]

NAMES_GIRL = ["Mara", "Ivy", "Lena", "Nia", "Tess", "June"]
NAMES_BOY = ["Ned", "Owen", "Finn", "Jules", "Ben", "Theo"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A tow is concerning if a wildebeest is towing something in the bike lane.
towing_issue(W, T) :- wildebeest(W), tow_item(T), in_lane(W), in_lane(T), towing(W, T).

% The bike lane is blocked when the tow item is in the lane and the path is not clear.
blocked_lane(T) :- tow_item(T), in_lane(T), towing(_, T).

% A cautionary fix exists when the detective redirects the tow out of the lane.
safe_fix(W, T) :- towing_issue(W, T), move_out(T).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("lane", "bike_lane")]
    lines.append(asp.fact("wildebeest", "wildebeest"))
    lines.append(asp.fact("detective", "Mara"))
    lines.append(asp.fact("witness", "Ned"))
    for tid in TOW_ITEMS:
        lines.append(asp.fact("tow_item", tid))
    lines.append(asp.fact("in_lane", "wildebeest"))
    lines.append(asp.fact("in_lane", "bike_cart"))
    lines.append(asp.fact("towing", "wildebeest", "bike_cart"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show towing_issue/2.\n#show blocked_lane/1.\n#show safe_fix/2."))
    atoms = set()
    for sym in model:
        atoms.add((sym.name, tuple(str(a) for a in sym.arguments)))
    expected = {
        ("towing_issue", ("wildebeest", "bike_cart")),
        ("blocked_lane", ("bike_cart",)),
    }
    if expected.issubset(atoms):
        print("OK: ASP rules match the Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP and Python reasoning disagree.")
    return 1


# ---------------------------------------------------------------------------
# Core reasoning
# ---------------------------------------------------------------------------

def is_reasonable(params: StoryParams) -> bool:
    return params.location == "bike_lane" and params.animal_name.lower() == "wildebeest" and params.tow_item in TOW_ITEMS


def explain_invalid(params: StoryParams) -> str:
    return "This story needs a wildebeest towing something in the bike lane."


def build_world(params: StoryParams) -> World:
    if not is_reasonable(params):
        raise StoryError(explain_invalid(params))

    world = World(SETTING)
    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label="detective",
        meters={"distance": 0.0},
        memes={"curiosity": 1.0, "caution": 1.0},
    ))
    witness = world.add(Entity(
        id=params.witness_name,
        kind="character",
        type=params.witness_type,
        label="witness",
        meters={"distance": 8.0},
        memes={"nervousness": 0.5},
    ))
    beast = world.add(Entity(
        id="wildebeest",
        kind="character",
        type="wildebeest",
        label="wildebeest",
        phrase="a dusty wildebeest with a bent horn",
        meters={"distance": 3.0, "tow_force": 1.0},
        memes={"tired": 0.4, "stubborn": 0.7},
    ))
    tow_item = world.add(Entity(
        id=params.tow_item,
        kind="thing",
        type=TOW_ITEMS[params.tow_item].kind,
        label=TOW_ITEMS[params.tow_item].label,
        phrase=TOW_ITEMS[params.tow_item].phrase,
        in_lane=True,
        towed_by="wildebeest",
        meters={"blocked": 1.0, "risk": 1.0},
        memes={"alarm": 0.8},
    ))

    # Act 1: setup.
    world.say(
        f"{detective.id} was a careful detective who liked quiet clues and clean answers."
    )
    world.say(
        f"One afternoon, {detective.id} rode along {world.setting.place} and spotted "
        f"{beast.phrase} pulling {tow_item.phrase} right across the lane."
    )
    world.say(
        f"{witness.id} stood nearby and pointed down the stripe of paint. "
        f'"Something is wrong there," {witness.pronoun()} whispered.'
    )

    # Act 2: tension.
    world.para()
    detective.memes["suspicion"] = 1.0
    detective.meters["distance"] = 1.0
    world.say(
        f"{detective.id} slowed down, because a tow in the bike lane could make riders crash."
    )
    world.say(
        f"{detective.id} followed the marks on the pavement and saw the cart scrape the edge."
    )
    world.say(
        f"The clue was plain: the lane was getting blocked, and the wildebeest looked too tired to notice."
    )

    # Act 3: turn and resolution.
    world.para()
    world.say(
        f'{detective.id} spoke gently: "You can keep moving, but not here. Let\'s get the tow out of the bike lane."'
    )
    tow_item.in_lane = False
    tow_item.towed_by = None
    beast.memes["stubborn"] = 0.0
    beast.memes["relief"] = 1.0
    detective.memes["suspicion"] = 0.0
    detective.memes["relief"] = 1.0
    tow_item.meters["blocked"] = 0.0
    world.say(
        f"{witness.id} helped steer the cart to the side path. Soon the stripe of the bike lane was open again."
    )
    world.say(
        f"The wildebeest snorted softly, the detective nodded, and the whole road felt safe and bright."
    )

    world.facts.update(
        detective=detective,
        witness=witness,
        beast=beast,
        tow_item=tow_item,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    return [
        'Write a cautionary detective story about a wildebeest towing something in a bike lane.',
        f"Tell a short story where {detective.id} notices a tow blocking {world.setting.place} and solves the problem kindly.",
        "Write a child-friendly mystery with clues, a wildebeest, and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    witness = f["witness"]
    beast = f["beast"]
    tow_item = f["tow_item"]
    return [
        QAItem(
            question=f"Who noticed the tow in the bike lane first?",
            answer=f"{detective.id} noticed it first and treated it like a clue.",
        ),
        QAItem(
            question=f"What was the wildebeest doing that caused trouble?",
            answer=f"The wildebeest was towing {tow_item.phrase} across the bike lane.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{witness.id} helped move the tow out of the lane, and the road became safe again.",
        ),
        QAItem(
            question=f"Why was the detective worried?",
            answer="Because a blocked bike lane could make riders stumble or crash.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and solves mysteries.",
        ),
        QAItem(
            question="What is towing?",
            answer="Towing means pulling something behind you with a rope, a hitch, or another connection.",
        ),
        QAItem(
            question="What is a bike lane for?",
            answer="A bike lane is a special part of the road for bicycles to ride safely.",
        ),
        QAItem(
            question="Why should a bike lane stay clear?",
            answer="It should stay clear so riders have enough space and do not get hurt.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 2) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 2) for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: type={ent.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary detective story about a wildebeest tow in a bike lane.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--detective-name")
    ap.add_argument("--witness-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    detective_name = args.detective_name or rng.choice(NAMES_GIRL + NAMES_BOY)
    witness_name = args.witness_name or rng.choice([n for n in NAMES_GIRL + NAMES_BOY if n != detective_name])
    detective_type = "girl" if detective_name in NAMES_GIRL else "boy"
    witness_type = "girl" if witness_name in NAMES_GIRL else "boy"
    return StoryParams(
        seed=args.seed,
        detective_name=detective_name,
        detective_type=detective_type,
        witness_name=witness_name,
        witness_type=witness_type,
        animal_name="Wildebeest",
        tow_item="bike_cart",
        location="bike_lane",
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    return asp_check()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show towing_issue/2.\n#show blocked_lane/1.\n#show safe_fix/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show towing_issue/2.\n#show blocked_lane/1.\n#show safe_fix/2."))
        print("ASP model:")
        for atom in sorted((sym.name, [str(a) for a in sym.arguments]) for sym in model):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
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
