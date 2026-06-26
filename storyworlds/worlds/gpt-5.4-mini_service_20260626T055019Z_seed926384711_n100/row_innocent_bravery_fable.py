#!/usr/bin/env python3
"""
storyworlds/worlds/row_innocent_bravery_fable.py
=================================================

A tiny fable-like storyworld about an innocent helper, a noisy row, and a
brave choice that quiets the trouble.

Seed premise:
- A small, innocent creature gets caught in a row.
- Bravery is not the same as loudness; it is choosing the kind path that keeps
  everyone safe.
- The turn comes when the brave one speaks or acts with steady care, and the
  row ends with trust restored.

The world is intentionally small and constraint-checked:
- one setting: a pond-edge village green
- one kind of conflict: a row over a shared boat seat, lantern, or basket
- one kind of resolution: a brave, reasonable compromise
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
# Entities and world state
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "goat", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the village green"
    still_water: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Row:
    id: str
    verb: str
    noun: str
    noise: str
    risk: str
    upset: str
    calming: str
    keyword: str = "row"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    owner_kind: str = "thing"


@dataclass
class BraveryGear:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

SETTING = Setting(
    place="the village green by the pond",
    still_water=True,
    affords={"row", "gather"},
)

ROWS = {
    "boat_seat": Row(
        id="boat_seat",
        verb="share the rowboat seat",
        noun="row",
        noise="a sharp row",
        risk="tip the little rowboat and splash the baskets",
        upset="the row was getting too loud",
        calming="a steadier way to share",
        tags={"row", "boat", "share", "pond"},
    ),
    "lantern": Row(
        id="lantern",
        verb="keep the lantern for one side",
        noun="row",
        noise="a rude row",
        risk="make the lantern wobble and go dark",
        upset="the row kept bouncing like a stone",
        calming="a fair turn with the lantern",
        tags={"row", "light", "share"},
    ),
}

PRIZES = {
    "boat": Prize(
        label="rowboat",
        phrase="a little painted rowboat",
        type="boat",
    ),
    "lantern": Prize(
        label="lantern",
        phrase="a small brass lantern",
        type="lantern",
    ),
    "basket": Prize(
        label="basket",
        phrase="a berry basket",
        type="basket",
    ),
}

BRAVERY_GEAR = {
    "steady_voice": BraveryGear(
        id="steady_voice",
        label="a steady voice",
        prep="take a slow breath and speak with a steady voice",
        tail="kept speaking gently until the row grew small",
        helps={"row"},
    ),
    "helping_hands": BraveryGear(
        id="helping_hands",
        label="helping hands",
        prep="offer helping hands and a fair turn",
        tail="showed that kindness can be brave",
        helps={"row", "share"},
    ),
}

CHARACTER_NAMES = ["Milo", "Pip", "Hazel", "Nina", "Otto", "Fern", "Toby", "Luna"]
ANIMAL_TYPES = ["mouse", "duck", "goat", "sparrow", "rabbit", "squirrel"]
HELPER_TYPES = ["mouse", "duck", "goat", "sparrow", "rabbit", "squirrel"]
TRAITS = ["innocent", "small", "careful", "gentle", "shy", "brave"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when a row conflict can actually be soothed by a bravery tool.
row_conflict(R) :- row(R).
has_fix(R) :- row_conflict(R), bravery(G), helps(G, row).

valid_story(P, R) :- setting(P), row(R), has_fix(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "pond_green"))
    lines.append(asp.fact("row", "boat_seat"))
    lines.append(asp.fact("row", "lantern"))
    for gid in BRAVERY_GEAR:
        lines.append(asp.fact("bravery", gid))
    for gid, gear in BRAVERY_GEAR.items():
        for tag in sorted(gear.helps):
            lines.append(asp.fact("helps", gid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

def row_at_risk(row: Row, prize: Prize) -> bool:
    if row.id == "boat_seat":
        return prize.label in {"rowboat", "basket"}
    if row.id == "lantern":
        return prize.label == "lantern"
    return False


def select_bravery(row: Row, prize: Prize) -> Optional[BraveryGear]:
    for gear in BRAVERY_GEAR.values():
        if "row" in gear.helps and row.id in {"boat_seat", "lantern"}:
            return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for rid, row in ROWS.items():
        for pid, prize in PRIZES.items():
            if row_at_risk(row, prize) and select_bravery(row, prize):
                combos.append((rid, pid))
    return combos


def _story_name(rng: random.Random, gender: str) -> str:
    return rng.choice(CHARACTER_NAMES)


@dataclass
class StoryParams:
    row: str
    prize: str
    hero: str
    helper: str
    hero_kind: str
    helper_kind: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable storyworld about an innocent row and a brave answer.")
    ap.add_argument("--row", choices=ROWS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--hero-kind", choices=ANIMAL_TYPES)
    ap.add_argument("--helper-kind", choices=HELPER_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.row and args.prize:
        row = ROWS[args.row]
        prize = PRIZES[args.prize]
        if not row_at_risk(row, prize):
            raise StoryError("This row and prize do not naturally belong in the same little fable.")
    combos = valid_combos()
    if args.row:
        combos = [c for c in combos if c[0] == args.row]
    if args.prize:
        combos = [c for c in combos if c[1] == args.prize]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    row_id, prize_id = rng.choice(sorted(combos))
    hero_kind = args.hero_kind or rng.choice(ANIMAL_TYPES)
    helper_kind = args.helper_kind or rng.choice(HELPER_TYPES)
    hero = args.hero or _story_name(rng, "any")
    helper = args.helper or _story_name(rng, "any")
    trait = args.trait or "innocent"
    return StoryParams(
        row=row_id,
        prize=prize_id,
        hero=hero,
        helper=helper,
        hero_kind=hero_kind,
        helper_kind=helper_kind,
        trait=trait,
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, helper: Entity, prize: Entity, row: Row) -> None:
    world.say(
        f"Near {world.setting.place}, {hero.name_or_label()} was an {hero.pronoun('possessive')} "
        f"{hero.type} with an {world.facts['trait']} heart. {hero.pronoun().capitalize()} loved "
        f"the little things that stayed bright and clean."
    )
    world.say(
        f"{helper.name_or_label()} was a {helper.type} who liked peace, but a {row.noise} had begun "
        f"over {prize.phrase}."
    )
    hero.memes["innocence"] = 1
    hero.memes["curiosity"] = 1
    helper.memes["calm"] = 1


def tension(world: World, hero: Entity, helper: Entity, prize: Entity, row: Row) -> None:
    hero.memes["concern"] = 1
    helper.memes["friction"] = 1
    world.say(
        f"The row started over {prize.name_or_label()}: one wanted it first, and the other thought that "
        f"was not fair. Soon {row.upset}."
    )
    world.say(
        f"If the quarrel went on, it could {row.risk}. Even the pond reeds seemed to lean closer and listen."
    )


def brave_turn(world: World, hero: Entity, helper: Entity, prize: Entity, row: Row, gear: BraveryGear) -> None:
    hero.memes["bravery"] = 1
    helper.memes["bravery"] = 1
    world.say(
        f"Then the innocent one grew brave. {hero.name_or_label().capitalize()} chose not to shout back, but to "
        f"{gear.prep}."
    )
    world.say(
        f"{helper.name_or_label()} heard that brave choice and followed it. Together they found {row.calming}."
    )
    world.say(
        f"At last, the row ended. {prize.name_or_label().capitalize()} was shared safely, and the pond went quiet again."
    )


def moral_image(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    world.say(
        f"By dusk, {hero.name_or_label()} and {helper.name_or_label()} were sitting side by side, "
        f"with {prize.name_or_label()} still safe between them. The innocent heart had learned that bravery "
        f"can be gentle."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    row = ROWS[params.row]
    prize = PRIZES[params.prize]

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_kind, label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_kind, label=params.helper))
    thing = world.add(Entity(id="prize", kind="thing", type=prize.type, label=prize.label, phrase=prize.phrase))
    world.facts = {
        "row": row,
        "prize": thing,
        "trait": params.trait,
        "hero": hero,
        "helper": helper,
        "gear": select_bravery(row, prize),
    }

    introduce(world, hero, helper, thing, row)
    world.para()
    tension(world, hero, helper, thing, row)
    world.para()
    brave_turn(world, hero, helper, thing, row, world.facts["gear"])
    moral_image(world, hero, helper, thing)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for children about an innocent {f["hero"].type} and a brave choice during a row.',
        f"Tell a small moral story where {f['hero'].name_or_label()} helps end a row over {f['prize'].label}.",
        f'Write a gentle story with the word "row" that ends with bravery and kindness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prize: Entity = f["prize"]
    row: Row = f["row"]
    gear: BraveryGear = f["gear"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who was the innocent character in the story?",
            answer=f"{hero.name_or_label()} was the innocent {hero.type} who did not want the row to grow mean.",
        ),
        QAItem(
            question=f"What was the row about?",
            answer=f"It was about {prize.name_or_label()}, and the argument made everyone tense until they found a fair way to share it.",
        ),
        QAItem(
            question=f"What brave thing helped end the row?",
            answer=f"{hero.name_or_label()} chose to {gear.prep}, and that calm brave act helped the others settle down.",
        ),
        QAItem(
            question=f"How did the story show bravery?",
            answer=f"It showed bravery when {hero.name_or_label()} stayed gentle even during the row and chose a peaceful answer instead of a louder fight.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel nervous or unsure.",
        ),
        QAItem(
            question="What is a row?",
            answer="A row is a noisy argument or quarrel, especially when people are upset with each other.",
        ),
        QAItem(
            question="What does innocent mean?",
            answer="Innocent means not mean or guilty, and often it means kind, untouched, or harmless.",
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
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {e.label or e.id} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(row="boat_seat", prize="boat", hero="Milo", helper="Hazel", hero_kind="mouse", helper_kind="duck", trait="innocent"),
    StoryParams(row="lantern", prize="lantern", hero="Fern", helper="Otto", hero_kind="rabbit", helper_kind="goat", trait="gentle"),
]


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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_cli_args() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for row_id, prize_id in combos:
            print(f"  {row_id:10} {prize_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.hero}: {p.row} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.row:
        combos = [c for c in combos if c[0] == args.row]
    if args.prize:
        combos = [c for c in combos if c[1] == args.prize]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    row_id, prize_id = rng.choice(sorted(combos))
    return StoryParams(
        row=row_id,
        prize=prize_id,
        hero=args.hero or rng.choice(CHARACTER_NAMES),
        helper=args.helper or rng.choice(CHARACTER_NAMES),
        hero_kind=args.hero_kind or rng.choice(ANIMAL_TYPES),
        helper_kind=args.helper_kind or rng.choice(HELPER_TYPES),
        trait=args.trait or rng.choice(TRAITS),
    )


if __name__ == "__main__":
    main()
