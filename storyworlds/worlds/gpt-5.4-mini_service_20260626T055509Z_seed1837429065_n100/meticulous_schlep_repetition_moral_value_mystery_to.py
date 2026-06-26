#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/meticulous_schlep_repetition_moral_value_mystery_to.py
==================================================================================================

A standalone storyworld for a small Space Adventure mystery:
- a careful crew,
- a repeated schlep through the station,
- a moral choice about honesty versus convenience,
- and a mystery to solve before launch.

The core premise:
A child crewmate keeps noticing that a tiny drone's cargo keeps vanishing from the
same moonport locker. The crew must investigate with meticulous care, repeat the
same route through the station, and decide whether to tell the commander the
truth about a shortcut that caused the trouble.

The story stays small, state-driven, and child-facing: the physical meters are
oxygen, charge, cargo, and distance; the emotional memes are worry, trust,
pride, and relief.
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Station:
    name: str = "the moonport station"
    route: list[str] = field(default_factory=lambda: ["dock", "corridor", "locker bay", "command nook"])
    mystery: str = "missing cargo"
    moral_value: str = "tell the truth"


@dataclass
class CrewRole:
    type: str
    label: str
    phrase: str
    bravery: str


@dataclass
class Cargo:
    label: str
    phrase: str
    region: str
    worth: str


@dataclass
class Clue:
    label: str
    place: str
    reveal: str


class World:
    def __init__(self, station: Station) -> None:
        self.station = station
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.station)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------
STATION = Station()

ROLES = {
    "pilot": CrewRole("pilot", "pilot", "a bright pilot", "careful"),
    "engineer": CrewRole("engineer", "engineer", "a steady engineer", "meticulous"),
    "scout": CrewRole("scout", "scout", "a curious scout", "alert"),
    "captain": CrewRole("captain", "captain", "a kind captain", "wise"),
}

CARGOES = {
    "samples": Cargo("sample canisters", "tiny sample canisters", "locker bay", "important"),
    "crystals": Cargo("crystal crates", "glittering crystal crates", "locker bay", "fragile"),
    "snacks": Cargo("snack packets", "sealed snack packets", "locker bay", "shared"),
}

CLUES = [
    Clue("scratch", "the hatch", "a loose latch had been dragging the lid open"),
    Clue("prints", "the floor", "tiny boot prints pointed back toward the shortcut"),
    Clue("tape", "the side panel", "a strip of tape had been used to hold the lock shut"),
]

SEED_WORDS = {"meticulous", "schlep", "repetition"}


# ---------------------------------------------------------------------------
# Reasonable story constraints
# ---------------------------------------------------------------------------
def plausible_mystery(role: CrewRole, cargo: Cargo) -> bool:
    return True


def plausible_moral(choice: str) -> bool:
    return choice in {"honesty", "shortcut"}


def choose_clue(rng: random.Random) -> Clue:
    return rng.choice(CLUES)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery exists when cargo goes missing from the locker bay.
mystery(missing_cargo) :- cargo(C).
missing(C) :- cargo(C), locker_bay(B), route(B).

% A clue solves the mystery when it points to the same place that cargo vanished.
solves(scratch) :- clue(scratch), missing(samples).
solves(prints) :- clue(prints), missing(crystals).
solves(tape) :- clue(tape), missing(snacks).

% A moral choice is good when the crew tells the truth after finding the clue.
moral_value(honesty) :- solved, truth_told.

% A valid story needs cargo, a clue, a mystery, and a moral value.
valid_story(Role, Cargo, Clue) :- crew(Role), cargo(Cargo), clue(Clue), solves(Clue), moral_value(honesty).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("station", "moonport"))
    lines.append(asp.fact("locker_bay", "bay"))
    lines.append(asp.fact("route", "dock"))
    lines.append(asp.fact("route", "corridor"))
    lines.append(asp.fact("route", "locker_bay"))
    lines.append(asp.fact("route", "command_nook"))
    for rid in ROLES:
        lines.append(asp.fact("crew", rid))
    for cid in CARGOES:
        lines.append(asp.fact("cargo", cid))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue.label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_story_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def valid_story_combos() -> list[tuple[str, str, str]]:
    return [(role, cargo, clue.label) for role in ROLES for cargo in CARGOES for clue in CLUES]


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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def solve_mystery(world: World, crew: Entity, cargo: Entity, clue: Clue) -> None:
    if ("solve", clue.label) in world.fired:
        return
    world.fired.add(("solve", clue.label))
    crew.memes["relief"] = crew.memes.get("relief", 0) + 1
    crew.memes["trust"] = crew.memes.get("trust", 0) + 1
    world.say(
        f"Carefully, {crew.id} checked the {clue.place} and found that {clue.reveal}."
    )


def repeat_schlep(world: World, crew: Entity, cargo: Entity) -> None:
    if ("schlep", cargo.id) in world.fired:
        return
    world.fired.add(("schlep", cargo.id))
    crew.meters["distance"] = crew.meters.get("distance", 0) + 1
    crew.memes["worry"] = crew.memes.get("worry", 0) + 1
    world.say(
        f"Again and again, {crew.id} had to schlep across the station with the cargo box, "
        f"trying not to bump the walls."
    )


def tell_truth(world: World, crew: Entity, captain: Entity, cargo: Entity, clue: Clue) -> None:
    if ("truth", clue.label) in world.fired:
        return
    world.fired.add(("truth", clue.label))
    captain.memes["trust"] = captain.memes.get("trust", 0) + 1
    crew.memes["pride"] = crew.memes.get("pride", 0) + 1
    world.say(
        f"Then {crew.id} told {captain.id} the truth about the shortcut and the loose hatch, "
        f"even though it was a little embarrassing."
    )
    world.say(
        f"{captain.id} nodded, because being honest was the right moral value, and "
        f"together they fixed the latch so the cargo stayed safe."
    )


def tell_story(world: World, hero: Entity, captain: Entity, cargo: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} was {hero.phrase} aboard {world.station.name}, and {hero.pronoun('subject')} "
        f"loved solving little space problems with {hero.pronoun('possessive')} careful hands."
    )
    world.say(
        f"On this trip, the crew needed to move {cargo.phrase} through the station, and "
        f"the {world.station.mystery} kept happening in the same place."
    )
    world.para()
    world.say(
        f"{hero.id} noticed the mystery first. The route to the locker bay took a lot of schlep, "
        f"and the same walk happened over and over again."
    )
    repeat_schlep(world, hero, cargo)
    world.say(
        f"That repetition made {hero.id} look closely instead of guessing."
    )
    solve_mystery(world, hero, cargo, clue)
    world.para()
    tell_truth(world, hero, captain, cargo, clue)
    world.say(
        f"In the end, the cargo was safe, the mystery was solved, and {hero.id} felt proud "
        f"for choosing the honest path."
    )


# ---------------------------------------------------------------------------
# Generation and QA
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    role: str
    cargo: str
    clue: str
    name: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short Space Adventure story about a meticulous crew member, a schlep, and a mystery to solve.',
        f"Tell a child-friendly story where {f['hero_name']} must solve a missing cargo mystery and choose honesty.",
        f'Write a gentle space-station story that uses the words "meticulous", "schlep", and "repetition".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    cargo = f["cargo"]
    clue = f["clue"]
    return [
        QAItem(
            question=f"What mystery was happening at {world.station.name}?",
            answer=f"The mystery was that {cargo.phrase} kept disappearing from the locker bay.",
        ),
        QAItem(
            question=f"How did {hero.id} help solve the mystery?",
            answer=f"{hero.id} looked carefully, noticed the clue about {clue.reveal}, and used that detail to solve the missing cargo mystery.",
        ),
        QAItem(
            question=f"What moral choice did {hero.id} make at the end?",
            answer=f"{hero.id} chose honesty and told {captain.id} the truth about the shortcut and the loose hatch.",
        ),
        QAItem(
            question=f"Why did the repeated trip through the station matter?",
            answer=f"The repetition made {hero.id} pay close attention, which helped spot the clue instead of rushing past it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does meticulous mean?",
            answer="Meticulous means very careful and paying attention to small details.",
        ),
        QAItem(
            question="What does schlep mean?",
            answer="A schlep is a long or tiring trip while carrying something heavy or awkward.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing the same thing again and again.",
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


def make_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    world = World(STATION)
    role = ROLES[params.role]
    cargo = CARGOES[params.cargo]
    clue = next(c for c in CLUES if c.label == params.clue)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=role.type,
        label=role.label,
        phrase=role.phrase,
        meters={"distance": 0.0},
        memes={"worry": 0.0, "trust": 0.0, "pride": 0.0, "relief": 0.0},
    ))
    captain = world.add(Entity(
        id="Captain",
        kind="character",
        type="captain",
        label="captain",
        phrase="the captain",
        meters={"distance": 0.0},
        memes={"trust": 0.0},
    ))
    cargo_ent = world.add(Entity(
        id="Cargo",
        kind="thing",
        type="cargo",
        label=cargo.label,
        phrase=cargo.phrase,
        owner=hero.id,
        caretaker=captain.id,
        plural=True if "crates" in cargo.label else False,
    ))
    world.facts = {
        "hero": hero,
        "captain": captain,
        "cargo": cargo_ent,
        "clue": clue,
        "hero_name": hero.id,
    }

    tell_story(world, hero, captain, cargo_ent, clue)
    return world


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
NAMES = ["Mina", "Jett", "Arlo", "Nova", "Pip", "Lina", "Tao", "Rin"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure mystery storyworld.")
    ap.add_argument("--role", choices=sorted(ROLES))
    ap.add_argument("--cargo", choices=sorted(CARGOES))
    ap.add_argument("--clue", choices=[c.label for c in CLUES])
    ap.add_argument("--name")
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
    if args.role and args.cargo and args.clue:
        if not plausible_mystery(ROLES[args.role], CARGOES[args.cargo]):
            raise StoryError("No reasonable mystery fits those choices.")
    roles = [args.role] if args.role else list(ROLES)
    cargos = [args.cargo] if args.cargo else list(CARGOES)
    clues = [args.clue] if args.clue else [c.label for c in CLUES]
    combos = [(r, c, k) for r in roles for c in cargos for k in clues]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    role, cargo, clue = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(role=role, cargo=cargo, clue=clue, name=name)


def valid_story_combos() -> list[tuple]:
    return [(r, c, k.label) for r in ROLES for c in CARGOES for k in CLUES]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
        combos = asp_valid_combos()
        print(f"{len(combos)} valid stories:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for role in ROLES:
            for cargo in CARGOES:
                for clue in CLUES:
                    params = StoryParams(role=role, cargo=cargo, clue=clue.label, name="Nova", seed=base_seed)
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
