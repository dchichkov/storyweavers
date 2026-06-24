#!/usr/bin/env python3
"""
storyworlds/worlds/peasant_brig_teamwork_lesson_learned_space_adventure.py
===========================================================================

A small storyworld about a peasant and a brig in a space adventure.

Premise:
A peasant caretaker brings supplies to a small brig spaceship. The ship is
supposed to deliver seed crates to a distant moon garden, but a broken cargo
lock and a drifting crate create a problem.

Turn:
The peasant tries to handle everything alone, but that makes the mistake worse.
The brig captain notices the trouble and insists on teamwork. Together they
use simple tools, divide the work, and steady the ship.

Resolution:
They fix the cargo, deliver the supplies, and learn that space jobs go better
when everyone helps.

This is a self-contained storyworld script with:
- typed entities with meters and memes
- a reasonableness gate plus inline ASP twin
- story generation, QA, JSON, trace, and verification support
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"peasant", "captain", "pilot", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    place: str
    cargo_hold: str
    route: str
    hull_type: str = "brig"


@dataclass
class Cargo:
    label: str
    phrase: str
    type: str
    fragile: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str] = field(default_factory=set)


class World:
    def __init__(self, ship: Ship) -> None:
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "moonport": Ship(name="Bright Comet", place="the moonport dock", cargo_hold="cargo hold", route="moon garden route"),
    "orbit": Ship(name="Bright Comet", place="the star lane", cargo_hold="cargo hold", route="moon garden route"),
    "asteroid": Ship(name="Bright Comet", place="the asteroid station", cargo_hold="cargo hold", route="moon garden route"),
}

TOOLS = {
    "strap": Tool(id="strap", label="a soft cargo strap", phrase="a soft cargo strap", helps_with={"drift", "cargo"}),
    "lamp": Tool(id="lamp", label="a bright deck lamp", phrase="a bright deck lamp", helps_with={"dark", "search"}),
    "scanner": Tool(id="scanner", label="a tiny scanner", phrase="a tiny scanner", helps_with={"lock", "cargo"}),
}

CARGOES = {
    "seeds": Cargo(label="seed crates", phrase="heavy seed crates for the moon garden", type="crates"),
    "fruit": Cargo(label="fruit boxes", phrase="fruit boxes for the outpost kitchen", type="boxes"),
    "parts": Cargo(label="spare parts", phrase="spare parts for the repair bay", type="parts"),
}

PEASANT_NAMES = ["Milo", "Nia", "Tess", "Rian", "Pia", "Jori"]
BRIG_NAMES = ["Captain Reed", "Captain Sol", "Captain Vega", "Captain Nora"]


@dataclass
class StoryParams:
    place: str
    cargo: str
    peasant_name: str
    brig_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure storyworld about teamwork and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--name")
    ap.add_argument("--brig-name")
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


def reasonableness_gate(place: str, cargo: str) -> bool:
    return place in SETTINGS and cargo in CARGOES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    cargo = args.cargo or rng.choice(list(CARGOES))
    if not reasonableness_gate(place, cargo):
        raise StoryError("The requested space trip does not form a valid story.")
    peasant_name = args.name or rng.choice(PEASANT_NAMES)
    brig_name = args.brig_name or rng.choice(BRIG_NAMES)
    return StoryParams(place=place, cargo=cargo, peasant_name=peasant_name, brig_name=brig_name)


def select_tool(problem: str) -> Optional[Tool]:
    for tool in TOOLS.values():
        if problem in tool.helps_with:
            return tool
    return None


def predict_fix(world: World, cargo: Cargo) -> bool:
    return world.get("cargo").meters.get("loose", 0) < THRESHOLD and cargo.fragile


def tell(params: StoryParams) -> World:
    ship = SETTINGS[params.place]
    cargo = CARGOES[params.cargo]
    world = World(ship)
    peasant = world.add(Entity(id="peasant", kind="character", type="peasant", label=params.peasant_name, meters={}, memes={}))
    brig = world.add(Entity(id="brig", kind="character", type="captain", label=params.brig_name, meters={}, memes={}))
    crates = world.add(Entity(
        id="cargo",
        kind="thing",
        type=cargo.type,
        label=cargo.label,
        phrase=cargo.phrase,
        owner=peasant.id,
        caretaker=brig.id,
        meters={"loose": 0.0, "scratched": 0.0},
        memes={"hope": 1.0},
    ))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label="", phrase=""))

    world.say(
        f"At {ship.place}, {params.peasant_name} was a small peasant with careful hands, and {params.brig_name} "
        f"was the captain of the brig {ship.name}."
    )
    world.say(
        f"They were carrying {cargo.phrase} for the far moon garden, because the ship had a useful job to do."
    )

    world.para()
    world.say(
        f"One day, a cargo lock snapped open inside the {ship.cargo_hold}, and one crate started to wobble."
    )
    peasant.memes["worry"] = 1.0
    crates.meters["loose"] += 1.0
    world.say(
        f"{params.peasant_name} wanted to fix everything at once, but the crate slid harder when {peasant.pronoun()} rushed."
    )
    peasant.memes["stubborn"] = 1.0
    brig.memes["concern"] = 1.0

    world.para()
    world.say(
        f"{params.brig_name} saw the wobble and said, \"We need teamwork on this brig.\""
    )
    chosen = select_tool("straps" if "strap" in TOOLS else "cargo")
    if chosen is None:
        chosen = TOOLS["strap"]
    tool.label = chosen.label
    tool.phrase = chosen.phrase
    tool.type = "tool"
    tool.meters["useful"] = 1.0

    world.say(
        f"They found {chosen.phrase}: {params.peasant_name} held the crate still while {params.brig_name} tightened the strap."
    )
    peasant.memes["cooperate"] = 1.0
    brig.memes["cooperate"] = 1.0
    crates.meters["loose"] = 0.0
    crates.meters["scratched"] = 0.0
    world.fired.add(("fixed", cargo.label))
    world.say(
        f"The crate stopped shaking, and the cargo hold became calm again."
    )

    world.para()
    world.say(
        f"By the time the brig reached the moon garden, the seed crates were safe, and the little peasant smiled."
    )
    world.say(
        f"{params.peasant_name} learned that a hard job can feel much smaller when two crew members do it together."
    )
    world.say(
        f"{params.brig_name} nodded, because the brig sailed best when everyone helped."
    )

    world.facts.update(
        ship=ship,
        cargo=cargo,
        peasant=peasant,
        brig=brig,
        tool=chosen,
        fixed=True,
        place=params.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short space adventure about a peasant and a brig that teaches teamwork.",
        f"Tell a child-friendly story where {f['peasant'].label} and {f['brig'].label} fix {f['cargo'].label} together.",
        f"Write a simple story on a brig where a small problem becomes a lesson learned about working together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    peasant = f["peasant"]
    brig = f["brig"]
    cargo = f["cargo"]
    ship = f["ship"]
    return [
        QAItem(
            question=f"Who was the story about on the brig {ship.name}?",
            answer=f"It was about {peasant.label}, a peasant on the brig, and {brig.label}, the captain who helped with the trip.",
        ),
        QAItem(
            question=f"What problem did {peasant.label} and {brig.label} have with the {cargo.label}?",
            answer=f"A cargo lock snapped open, so the {cargo.label} started to wobble inside the cargo hold.",
        ),
        QAItem(
            question=f"How did they fix the trouble on the brig?",
            answer=f"They worked together: {peasant.label} held the crate steady while {brig.label} tightened the cargo strap.",
        ),
        QAItem(
            question="What lesson did the peasant learn?",
            answer="The peasant learned that teamwork makes a hard job easier and safer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a brig?",
            answer="A brig is a small sailing ship with two masts. In a space story, it can be imagined as a ship that travels between stars.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do a job together.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="It means understanding something important after an experience, so you can do better next time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(moonport).
valid_place(orbit).
valid_place(asteroid).

valid_cargo(seeds).
valid_cargo(fruit).
valid_cargo(parts).

valid_story(P, C) :- valid_place(P), valid_cargo(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("valid_place", p))
    for c in CARGOES:
        lines.append(asp.fact("valid_cargo", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(p, c) for p in SETTINGS for c in CARGOES if reasonableness_gate(p, c)}
    model = asp.one_model(asp_program("#show valid_story/2."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: ASP matches Python reasonableness gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="moonport", cargo="seeds", peasant_name="Milo", brig_name="Captain Vega"),
    StoryParams(place="orbit", cargo="fruit", peasant_name="Nia", brig_name="Captain Sol"),
    StoryParams(place="asteroid", cargo="parts", peasant_name="Tess", brig_name="Captain Reed"),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid space-adventure combos:")
        for p, c in stories:
            print(f"  {p}  {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        if args.all:
            p = sample.params
            header = f"### {p.peasant_name} and {p.brig_name} at {p.place} with {p.cargo}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
