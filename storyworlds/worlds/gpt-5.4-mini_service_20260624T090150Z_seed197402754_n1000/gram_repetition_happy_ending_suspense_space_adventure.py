#!/usr/bin/env python3
"""
A standalone story world for a small space-adventure domain.

Premise:
- A tiny crew travels to a moon base with a delicate cargo measured in grams.
- A repeated routine keeps the ship safe.
- Suspense builds when the cargo box drifts loose.
- A happy ending comes when the crew recovers it and lands home with the gram jar intact.

This world is intentionally small, child-facing, and state-driven.
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
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    place: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Station:
    name: str
    route: str
    repetition_count: int = 0
    safe_landing: bool = True


@dataclass
class Cargo:
    label: str
    mass_grams: int
    fragile: bool = True


@dataclass
class StoryParams:
    station: str
    cargo: str
    hero: str
    sidekick: str
    seed: Optional[int] = None


class World:
    def __init__(self, station: Station):
        self.station = station
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.suspense: float = 0.0
        self.repetition: int = 0

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

STATIONS = {
    "moonbase": Station(name="the moon base", route="moon"),
    "orbital_lab": Station(name="the orbital lab", route="orbit"),
    "asteroid_outpost": Station(name="the asteroid outpost", route="asteroid"),
}

CARGOS = {
    "gram_crystals": Cargo(label="gram crystals", mass_grams=3, fragile=True),
    "gram_jar": Cargo(label="a gram jar", mass_grams=12, fragile=True),
    "star_gram": Cargo(label="a star gram", mass_grams=1, fragile=True),
}

HERO_NAMES = ["Nia", "Zed", "Milo", "Tia", "Rio", "Pip", "Luna", "Nova"]
SIDEKICK_NAMES = ["Beep", "Dot", "Siri", "Moss", "Kip", "Echo"]

# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------


def _ship_routine(world: World, hero: Entity, cargo: Entity) -> None:
    world.repetition += 1
    world.station.repetition_count += 1
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    cargo.meters["secure"] = cargo.meters.get("secure", 0) + 1
    world.say(
        f"Every launch began the same way: check the straps, count the lights, and "
        f"count the {cargo.label} again."
    )


def _launch(world: World, hero: Entity, sidekick: Entity, cargo: Entity) -> None:
    hero.memes["excitement"] = hero.memes.get("excitement", 0) + 1
    sidekick.memes["excitement"] = sidekick.memes.get("excitement", 0) + 1
    cargo.carried_by = hero.id
    cargo.place = "ship"
    world.say(
        f"{hero.id} and {sidekick.id} climbed into the small silver ship, and the "
        f"{cargo.label} tucked safely beside the controls."
    )
    world.say(
        f"The ship hummed over {world.station.route} space, then farther on, until "
        f"the stars looked like tiny crumbs of light."
    )


def _suspense(world: World, hero: Entity, sidekick: Entity, cargo: Entity) -> None:
    world.suspense += 1
    cargo.carried_by = None
    cargo.place = "air"
    hero.memes["worry"] = hero.memes.get("worry", 0) + 2
    sidekick.memes["worry"] = sidekick.memes.get("worry", 2) + 1
    world.say(
        f"Then came a bump. The hatch clicked. The {cargo.label} drifted up, slow as a "
        f"sleepy moon pebble."
    )
    world.say(
        f"{hero.id} froze, because one little box could float behind the seat and vanish "
        f"into the dark."
    )


def _search_repeat(world: World, hero: Entity, sidekick: Entity, cargo: Entity) -> None:
    world.repetition += 1
    hero.memes["focus"] = hero.memes.get("focus", 0) + 1
    sidekick.memes["focus"] = sidekick.memes.get("focus", 0) + 1
    world.say(
        f"Again they checked the straps. Again they counted the lights. Again they "
        f"looked under the seat."
    )
    world.say(
        f"This time {sidekick.id} stretched a careful hand, and {hero.id} guided it "
        f"to the floating {cargo.label}."
    )
    cargo.carried_by = hero.id
    cargo.place = "ship"
    cargo.meters["secure"] = cargo.meters.get("secure", 0) + 1
    world.say(
        f"At last the {cargo.label} came home to its pouch with a soft plop."
    )


def _landing(world: World, hero: Entity, sidekick: Entity, cargo: Entity) -> None:
    world.station.safe_landing = True
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    sidekick.memes["joy"] = sidekick.memes.get("joy", 0) + 2
    cargo.place = "base"
    world.say(
        f"The ship dipped toward the blue home world. The landing lights blinked once, "
        f"twice, and then stayed bright."
    )
    world.say(
        f"{hero.id} and {sidekick.id} stepped out smiling, with the {cargo.label} still "
        f"safe and the mission complete."
    )
    world.say(
        f"That night, the little crew counted the gram crystals one more time, and every "
        f"one was there."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------


def tell(station: Station, cargo_cfg: Cargo, hero_name: str, sidekick_name: str) -> World:
    world = World(station)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="thing", label="robot sidekick"))
    cargo = world.add(Entity(id="cargo", kind="thing", label=cargo_cfg.label))

    world.say(
        f"{hero.id} was a tiny space explorer who loved shiny buttons and careful plans."
    )
    world.say(
        f"On the launch table sat {cargo.label}, and it weighed only {cargo_cfg.mass_grams} gram"
        f"{'s' if cargo_cfg.mass_grams != 1 else ''}."
    )
    world.say(
        f"{hero.id} liked that number, because saying gram, gram, gram made the mission feel "
        f"like a song."
    )

    world.para()
    _ship_routine(world, hero, cargo)
    _launch(world, hero, sidekick, cargo)

    world.para()
    _suspense(world, hero, sidekick, cargo)
    _search_repeat(world, hero, sidekick, cargo)

    world.para()
    _landing(world, hero, sidekick, cargo)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        cargo=cargo,
        station=station,
        cargo_cfg=cargo_cfg,
        suspense=world.suspense,
        repetition=world.repetition,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    cargo_cfg: Cargo = f["cargo_cfg"]
    return [
        f'Write a gentle space adventure about {hero.id} and a cargo box with the word "gram" in it.',
        f"Tell a story where {hero.id} keeps checking the same space cargo again and again before a scary floating moment.",
        f"Write a child-friendly spaceship story that ends happily with {cargo_cfg.label} safely home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    cargo: Entity = f["cargo"]
    station: Station = f["station"]
    cargo_cfg: Cargo = f["cargo_cfg"]

    return [
        QAItem(
            question=f"What did {hero.id} and {sidekick.id} carry on the mission?",
            answer=f"They carried {cargo.label}, which was a tiny fragile cargo measured in grams.",
        ),
        QAItem(
            question=f"What made the middle of the story suspenseful?",
            answer=f"The suspense came when the {cargo.label} drifted out of place and floated in the ship.",
        ),
        QAItem(
            question=f"How did the crew fix the problem?",
            answer=f"They searched again, followed their careful routine, and guided the {cargo.label} back into its pouch.",
        ),
        QAItem(
            question=f"What was the happy ending?",
            answer=f"The ship landed safely at {station.name}, and the {cargo.label} arrived home without getting lost.",
        ),
        QAItem(
            question=f"Why did the story repeat the check step more than once?",
            answer=f"The repeated check helped the crew stay calm and made sure the {cargo.label} stayed secure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gram?",
            answer="A gram is a very small unit used to measure how heavy something is.",
        ),
        QAItem(
            question="Why do space crews check their gear again and again?",
            answer="They check again and again so nothing slips, breaks, or drifts away during the trip.",
        ),
        QAItem(
            question="Why are space missions exciting?",
            answer="Space missions are exciting because the crew travels far away, solves problems, and discovers new places.",
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
        bits = []
        if e.place:
            bits.append(f"place={e.place}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  suspense={world.suspense}")
    lines.append(f"  repetition={world.repetition}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A cargo is fragile when it is a cargo that can drift away.
fragile_cargo(C) :- cargo(C), fragile(C).

% Suspense rises when fragile cargo is floating.
suspense(C) :- fragile_cargo(C), floating(C).

% Repetition is useful when the crew checks again.
repeat_step(check) :- repeated_check.

% Happy ending: the cargo is found and the ship lands safely.
happy_end(C) :- fragile_cargo(C), recovered(C), landed_safely.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in STATIONS.items():
        lines.append(asp.fact("station", sid))
        lines.append(asp.fact("route", sid, s.route))
    for cid, c in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("label", cid, c.label))
        lines.append(asp.fact("grams", cid, c.mass_grams))
        if c.fragile:
            lines.append(asp.fact("fragile", cid))
    lines.append(asp.fact("repeated_check"))
    lines.append(asp.fact("floating", "cargo"))
    lines.append(asp.fact("recovered", "cargo"))
    lines.append(asp.fact("landed_safely"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_end/1. #show suspense/1. #show repeat_step/1."))
    atoms = {(sym.name, tuple(arg.name if arg.type != arg.type.Number else arg.number for arg in sym.arguments))
             for sym in model}
    want = {("happy_end", ("cargo",)), ("suspense", ("cargo",)), ("repeat_step", ("check",))}
    if atoms == want:
        print("OK: ASP twin matches the Python story logic.")
        return 0
    print("MISMATCH between ASP twin and expected facts.")
    print("got:", sorted(atoms))
    print("want:", sorted(want))
    return 1


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with repetition, suspense, and a happy ending.")
    ap.add_argument("--station", choices=STATIONS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    station = args.station or rng.choice(list(STATIONS))
    cargo = args.cargo or rng.choice(list(CARGOS))
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    if hero == sidekick:
        raise StoryError("Hero and sidekick must be different.")
    return StoryParams(station=station, cargo=cargo, hero=hero, sidekick=sidekick)


def generate(params: StoryParams) -> StorySample:
    world = tell(STATIONS[params.station], CARGOS[params.cargo], params.hero, params.sidekick)
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
    StoryParams(station="moonbase", cargo="gram_jar", hero="Luna", sidekick="Beep"),
    StoryParams(station="orbital_lab", cargo="gram_crystals", hero="Nia", sidekick="Echo"),
    StoryParams(station="asteroid_outpost", cargo="star_gram", hero="Nova", sidekick="Dot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_end/1. #show suspense/1. #show repeat_step/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_end/1. #show suspense/1. #show repeat_step/1."))
        print("\n".join(sorted(str(a) for a in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
