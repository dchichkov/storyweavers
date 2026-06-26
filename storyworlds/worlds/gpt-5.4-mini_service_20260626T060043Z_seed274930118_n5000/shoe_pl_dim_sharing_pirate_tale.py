#!/usr/bin/env python3
"""
storyworlds/worlds/shoe_pl_dim_sharing_pirate_tale.py
=====================================================

A small, constraint-checked pirate tale world about sharing a treasured pair of
shoes on a dim little voyage.

Seed premise:
- shoe-pl-dim
- Sharing
- Pirate Tale style

The story world models a simple causality:
- A pirate child treasures a pair of shoes.
- The shoes matter for the voyage because the deck is dim, wet, and rough.
- Another crew member needs them for a turn on deck.
- A sharing choice changes the emotional state and the physical outcome.

The prose is intentionally child-facing, concrete, and story-driven.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {"dry": 0.0, "safe": 0.0, "used": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "worry": 0.0, "sharing": 0.0, "pride": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dim dock"
    dark: bool = True
    wet: bool = True
    breeze: str = "a salty breeze"


@dataclass
class StoryParams:
    name: str
    gender: str
    mate_name: str
    mate_gender: str
    prize: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
SETTING = Setting()

PRIZES = {
    "shoe-pl-dim": {
        "label": "shoes",
        "phrase": "a bright pair of shoes",
        "region": "feet",
        "plural": True,
        "special": "dim",
    }
}

CHILD_NAMES = ["Mira", "Niko", "Pip", "Tessa", "Jory", "Lena"]
CREW_NAMES = ["Captain Reed", "Bram", "Nell", "Sailor Finn", "Ivy", "Ro"]
TRAITS = ["brave", "cheerful", "curious", "lively"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A treasured item can be shared when another crew member needs it and the item
% is suited to the setting.
shareable(P) :- prize(P), treasured(P), fits_setting(P).

% Sharing resolves the worry when the treasure is passed willingly.
resolved(P) :- shareable(P), shared(P).

% A dim deck makes shoes useful, because it is easy to slip.
at_risk(P) :- prize(P), worn_on(P, feet), dim_place.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = [
        asp.fact("dim_place"),
        asp.fact("setting", "dock"),
        asp.fact("place", "dock", "dock"),
        asp.fact("prize", "shoe_pl_dim"),
        asp.fact("treasured", "shoe_pl_dim"),
        asp.fact("fits_setting", "shoe_pl_dim"),
        asp.fact("worn_on", "shoe_pl_dim", "feet"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    w = World(SETTING)
    hero = w.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        plural=False,
    ))
    mate = w.add(Entity(
        id=params.mate_name,
        kind="character",
        type=params.mate_gender,
        label=params.mate_name,
        plural=False,
    ))
    prize_cfg = PRIZES[params.prize]
    shoes = w.add(Entity(
        id="shoes",
        type="shoes",
        label=prize_cfg["label"],
        phrase=prize_cfg["phrase"],
        plural=prize_cfg["plural"],
        owner=hero.id,
        worn_by=hero.id,
        meters={"dry": 1.0, "safe": 1.0, "used": 0.0},
        memes={"joy": 1.0, "worry": 0.0, "sharing": 0.0, "pride": 1.0},
    ))
    w.facts.update(hero=hero, mate=mate, shoes=shoes, prize_cfg=prize_cfg)
    return w


def predict_need(world: World) -> bool:
    shoes = world.get("shoes")
    return shoes.meters["safe"] >= 1.0 and shoes.meters["dry"] >= 1.0


def share_shoes(world: World, hero: Entity, mate: Entity, shoes: Entity) -> None:
    shoes.memes["sharing"] += 1
    hero.memes["sharing"] += 1
    hero.memes["pride"] += 1
    mate.memes["joy"] += 1
    shoes.worn_by = mate.id
    shoes.meters["used"] += 1
    world.facts["shared"] = True
    world.say(
        f"{hero.id} smiled and shared the shoes with {mate.id}. "
        f"{hero.pronoun().capitalize()} tied the laces snug and handed them over with a nod."
    )


def wear_and_walk(world: World, wearer: Entity, shoes: Entity) -> None:
    shoes.worn_by = wearer.id
    shoes.meters["safe"] += 1
    shoes.meters["dry"] += 1
    world.say(
        f"{wearer.id} stepped onto the dim deck in the shoes, and the little pair kept the feet steady."
    )


def opening(world: World) -> None:
    hero = world.facts["hero"]
    shoes = world.facts["shoes"]
    world.say(
        f"On the dim dock by the sea, {hero.id} loved {hero.pronoun('possessive')} shoes more than a shiny coin."
    )
    world.say(
        f"The shoes were a bright pair, and they looked bold against the gray boards."
    )
    world.say(
        f"{hero.id} liked how the laces felt neat and how the shoes kept {hero.pronoun('possessive')} feet snug."
    )


def problem(world: World) -> None:
    hero = world.facts["hero"]
    mate = world.facts["mate"]
    shoes = world.facts["shoes"]
    world.para()
    world.say(
        f"One evening, the ship rocked softly, and the deck was so dim that the planks looked like dark stripes."
    )
    world.say(
        f"{mate.id} needed to cross the deck to help with the sail, but {mate.pronoun('subject')} had bare feet."
    )
    world.say(
        f"{hero.id} saw the wobble and worried, because the shoes were the only steady pair on board."
    )
    if predict_need(world):
        world.say(
            f"{hero.id} wanted to keep them close, yet {hero.pronoun('possessive')} heart tugged toward helping."
        )


def turn_to_sharing(world: World) -> None:
    hero = world.facts["hero"]
    mate = world.facts["mate"]
    shoes = world.facts["shoes"]
    world.para()
    world.say(
        f"Then {hero.id} took a breath and said, \"You can borrow them first.\""
    )
    share_shoes(world, hero, mate, shoes)
    world.say(
        f"{mate.id} beamed and thanked {hero.id}, because the shoes made the dim deck feel less spooky."
    )


def ending(world: World) -> None:
    hero = world.facts["hero"]
    mate = world.facts["mate"]
    shoes = world.facts["shoes"]
    world.para()
    wear_and_walk(world, mate, shoes)
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"At the end, {hero.id} watched {mate.id} cross the deck safely, and the shared shoes shone like a tiny lantern."
    )
    world.say(
        f"{hero.id} felt proud, because the best treasure on the ship was not keeping the shoes—it was sharing them."
    )


def build_story(params: StoryParams) -> World:
    world = setup_world(params)
    opening(world)
    problem(world)
    turn_to_sharing(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    return [
        f'Write a short pirate story for a young child about sharing {hero.pronoun("possessive")} shoes on a dim dock.',
        f"Tell a gentle pirate tale where {hero.id} helps {mate.id} by sharing a bright pair of shoes.",
        f"Write a simple story with a dim ship deck, a pair of shoes, and a happy sharing ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    shoes = f["shoes"]
    return [
        QAItem(
            question=f"Who owns the shoes at the start of the story?",
            answer=f"{hero.id} owns the shoes at the start, and {hero.pronoun('possessive')} feet wear them first.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry when {mate.id} needed help on the dim deck?",
            answer=(
                f"{hero.id} worried because the deck was dim and slippery, so the bright shoes could help keep "
                f"{mate.id} steady."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} do instead of keeping the shoes?",
            answer=(
                f"{hero.id} shared the shoes with {mate.id}, and that choice helped the crew cross the deck safely."
            ),
        ),
        QAItem(
            question=f"How did the story end for the shoes?",
            answer=(
                f"The shoes ended up worn safely on {mate.id}, and {hero.id} felt proud about sharing them."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something you have, often because it will help them or make them happy.",
        ),
        QAItem(
            question="Why are shoes useful on a deck?",
            answer="Shoes help feet stay steady and protected, especially when the deck is wet, rough, or dim.",
        ),
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright, so it can be hard to see clearly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} worn_by={e.worn_by} "
            f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Verification / ASP
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show shareable/1.\n#show resolved/1.\n#show at_risk/1."))
    atoms = set((sym.name, tuple(a.name if hasattr(a, "name") else a for a in sym.arguments)) for sym in model)
    expected = {("shareable", ("shoe_pl_dim",)), ("at_risk", ("shoe_pl_dim",))}
    if atoms >= expected:
        print("OK: ASP rules produce the expected facts.")
        return 0
    print("MISMATCH: ASP rules did not produce expected facts.")
    print("Got:", sorted(atoms))
    return 1


def show_asp() -> str:
    return asp_program("#show shareable/1.\n#show resolved/1.\n#show at_risk/1.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate story world about sharing shoes on a dim deck.")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mate-name", choices=CREW_NAMES)
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--prize", choices=PRIZES)
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
    if args.gender is None:
        args_gender = rng.choice(["girl", "boy"])
    else:
        args_gender = args.gender
    if args.mate_gender is None:
        mate_gender = "boy" if args_gender == "girl" else "girl"
    else:
        mate_gender = args.mate_gender
    name = args.name or rng.choice(CHILD_NAMES)
    mate_name = args.mate_name or rng.choice([n for n in CREW_NAMES if n != name])
    prize = args.prize or "shoe-pl-dim"
    if prize != "shoe-pl-dim":
        raise StoryError("Only the shoe-pl-dim treasure fits this small pirate tale world.")
    return StoryParams(name=name, gender=args_gender, mate_name=mate_name, mate_gender=mate_gender, prize=prize)


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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


def asp_listing() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show shareable/1.\n#show resolved/1.\n#show at_risk/1."))
    return [str(sym) for sym in model]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(show_asp())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(asp_listing()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mira", gender="girl", mate_name="Bram", mate_gender="boy", prize="shoe-pl-dim"),
            StoryParams(name="Niko", gender="boy", mate_name="Nell", mate_gender="girl", prize="shoe-pl-dim"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
