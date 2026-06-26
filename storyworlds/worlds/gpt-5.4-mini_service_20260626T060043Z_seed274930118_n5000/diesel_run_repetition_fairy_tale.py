#!/usr/bin/env python3
"""
storyworlds/worlds/diesel_run_repetition_fairy_tale.py
======================================================

A small fairy-tale story world about a little diesel runner, with repetition
as the main story instrument.

Seed image:
- A tiny diesel engine wants to run and run.
- The road is long, the fuel is low, and a kind helper must notice the need.
- The repeated running becomes a refrain, and the refilled engine reaches the
  castle gate in time.

This world keeps the tale simple, concrete, and state-driven:
fuel matters, distance matters, worry matters, and the ending proves what
changed.
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
# Core model
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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "king", "man", "miller"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    distance: int = 0


@dataclass
class Vehicle:
    id: str
    label: str
    phrase: str
    fuel_kind: str
    fuel_use: float
    speed: int
    route: str
    destination: str
    repetition: str = ""


@dataclass
class Fuel:
    id: str
    label: str
    phrase: str
    kind: str
    amount: float


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.route_remaining = setting.distance
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.route_remaining = self.route_remaining
        c.facts = copy.deepcopy(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "forest_road": Setting(place="the forest road", affords={"run"}, distance=3),
    "hill_road": Setting(place="the hill road", affords={"run"}, distance=4),
    "castle_lane": Setting(place="the castle lane", affords={"run"}, distance=2),
}

VEHICLES = {
    "diesel_wagon": Vehicle(
        id="diesel_wagon",
        label="little wagon",
        phrase="a little diesel wagon with a brass bell",
        fuel_kind="diesel",
        fuel_use=1.0,
        speed=1,
        route="run along the road",
        destination="the castle gate",
        repetition="run, run, run",
    ),
}

FUELS = {
    "diesel_can": Fuel(
        id="diesel_can",
        label="can of diesel",
        phrase="a bright can of diesel",
        kind="diesel",
        amount=3.0,
    ),
}

CHARACTER_NAMES = ["Lina", "Milo", "Nora", "Pip", "Timo", "Hana"]
HELPER_TYPES = ["miller", "queen", "gardener", "father", "mother"]
TRAITS = ["brave", "kind", "small", "cheerful", "patient"]


@dataclass
class StoryParams:
    place: str
    vehicle: str
    fuel: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for vehicle_id, vehicle in VEHICLES.items():
            if "run" not in setting.affords:
                continue
            for fuel_id, fuel in FUELS.items():
                if fuel.kind == vehicle.fuel_kind and fuel.amount >= vehicle.fuel_use * setting.distance:
                    out.append((place, vehicle_id, fuel_id))
    return out


def explain_rejection(place: str, vehicle: Vehicle, fuel: Fuel) -> str:
    if fuel.kind != vehicle.fuel_kind:
        return f"(No story: {vehicle.label} runs on {vehicle.fuel_kind}, not {fuel.kind}.)"
    need = vehicle.fuel_use * SETTINGS[place].distance
    return f"(No story: the road is too long for that much fuel; it needs at least {need:.0f} units of diesel.)"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def _move(world: World, rider: Entity, vehicle: Vehicle, narrate: bool = True) -> None:
    if world.route_remaining <= 0:
        return
    step = min(vehicle.speed, world.route_remaining)
    world.route_remaining -= step
    rider.meters["distance"] = rider.meters.get("distance", 0.0) + step
    rider.meters["fuel_spent"] = rider.meters.get("fuel_spent", 0.0) + vehicle.fuel_use * step
    if narrate:
        world.say(f"The little wagon could run, run, run, and each run carried it one step closer.")


def _consume_fuel(world: World, rider: Entity, can: Entity, vehicle: Vehicle) -> None:
    need = vehicle.fuel_use
    if can.meters.get("fuel", 0.0) < need:
        rider.memes["worry"] += 1
        return
    can.meters["fuel"] -= need
    rider.meters["fuel"] = rider.meters.get("fuel", 0.0) + need


def predict_trip(world: World, rider: Entity, vehicle: Vehicle, fuel: Entity) -> dict:
    sim = world.copy()
    s_rider = sim.get(rider.id)
    s_fuel = sim.get(fuel.id)
    while sim.route_remaining > 0 and s_fuel.meters.get("fuel", 0.0) >= vehicle.fuel_use:
        _consume_fuel(sim, s_rider, s_fuel, vehicle)
        _move(sim, s_rider, vehicle, narrate=False)
    return {"arrives": sim.route_remaining <= 0, "fuel_left": s_fuel.meters.get("fuel", 0.0)}


def tell(setting: Setting, vehicle_def: Vehicle, fuel_def: Fuel,
         hero_name: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", memes={"love_run": 0.0, "joy": 0.0, "worry": 0.0}))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    vehicle = world.add(Entity(
        id=vehicle_def.id, type="vehicle", label=vehicle_def.label, phrase=vehicle_def.phrase,
        owner=hero.id, meters={"fuel": 0.0}, memes={"speed": float(vehicle_def.speed)},
    ))
    fuel = world.add(Entity(
        id=fuel_def.id, type="fuel", label=fuel_def.label, phrase=fuel_def.phrase,
        owner=helper.id, meters={"fuel": fuel_def.amount},
    ))

    # Act 1
    world.say(f"Once upon a time, there was a {trait} little child named {hero.id}.")
    world.say(f"{hero.id} loved the {vehicle.label} and loved to run, run, run.")
    world.say(f"Beside the road stood {helper.label}, keeping a bright {fuel.label} safe.")

    # Act 2
    world.para()
    world.say(f"One day, {hero.id} wanted to {vehicle_def.route} to {vehicle_def.destination}.")
    pred = predict_trip(world, hero, vehicle_def, fuel)
    if not pred["arrives"]:
        world.say(f"But the little wagon could not go far on an empty tank.")
        world.say(f'"You need diesel before you can run, run, run," said {helper.label}.')
        hero.memes["worry"] += 1
        world.facts["need_diesel"] = True
        world.facts["predicted_arrival"] = False
    else:
        world.facts["need_diesel"] = False
        world.facts["predicted_arrival"] = True

    # Act 3
    world.para()
    if fuel.meters.get("fuel", 0.0) >= vehicle_def.fuel_use * setting.distance:
        world.say(f"{helper.label} poured diesel into the tank, little by little, until it was full.")
        hero.memes["joy"] += 1
        while world.route_remaining > 0:
            _consume_fuel(world, hero, fuel, vehicle_def)
            _move(world, hero, vehicle_def, narrate=True)
            if world.route_remaining > 0:
                world.say(f"Run, run, run went the wagon on the long road.")
        world.say(f"At last, {hero.id} reached {vehicle_def.destination}, and the brass bell rang in the wind.")
        world.say(f"The wagon had run, run, run, and the road was done.")
        hero.memes["joy"] += 2
        hero.memes["worry"] = 0
        world.facts["resolved"] = True
    else:
        world.say(f"No enough diesel meant no fair ending, so the story stays silent here.")
        world.facts["resolved"] = False

    world.facts.update(hero=hero, helper=helper, vehicle=vehicle, fuel=fuel, setting=setting, vehicle_def=vehicle_def, fuel_def=fuel_def)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    vehicle_def = f["vehicle_def"]
    return [
        'Write a short fairy tale about a little diesel runner who wants to run, run, run.',
        f"Tell a child-friendly story where {hero.id} must use diesel before {hero.pronoun()} can {vehicle_def.route}.",
        f'Write a repeating fairy tale that includes the word "diesel" and ends at {vehicle_def.destination}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    vehicle = f["vehicle"]
    fuel = f["fuel"]
    vehicle_def = f["vehicle_def"]
    place = f["setting"].place
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a small child who loved the {vehicle.label} and wanted to run, run, run.",
        ),
        QAItem(
            question=f"What did {helper.label} keep safe?",
            answer=f"{helper.label} kept {fuel.phrase} safe until the wagon needed diesel.",
        ),
        QAItem(
            question=f"Where did {hero.id} want to go?",
            answer=f"{hero.id} wanted to {vehicle_def.route} on {place} and reach {vehicle_def.destination}.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end?",
                answer=f"It ended with the tank full, the wagon running, running, running, and {vehicle_def.destination} finally reached.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "diesel": (
        "What is diesel?",
        "Diesel is a kind of fuel some engines use to make strong vehicles move.",
    ),
    "run": (
        "What does it mean to run?",
        "To run means to move quickly with many small steps, faster than walking.",
    ),
    "repetition": (
        "What is repetition in a story?",
        "Repetition is when a writer says the same word or line again to make it memorable.",
    ),
    "fairy_tale": (
        "What makes a story feel like a fairy tale?",
        "A fairy tale often begins with 'once upon a time,' has simple magic or wonder, and ends in a clear way.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
need_diesel(V) :- vehicle(V), fuel_kind(V, diesel), route_distance(P,D), fuel_use(V,U), D*U > 0, enough_fuel(V,F), F < D*U.
compatible(P, V, F) :- place(P), vehicle(V), fuel(F), fuel_kind(V, diesel), fuel_kind_of(F, diesel), route_distance(P,D), fuel_use(V,U), fuel_amount(F,A), A >= D*U.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("route_distance", pid, s.distance))
    for vid, v in VEHICLES.items():
        lines.append(asp.fact("vehicle", vid))
        lines.append(asp.fact("fuel_kind", vid, v.fuel_kind))
        lines.append(asp.fact("fuel_use", vid, int(v.fuel_use)))
    for fid, f in FUELS.items():
        lines.append(asp.fact("fuel", fid))
        lines.append(asp.fact("fuel_kind_of", fid, f.kind))
        lines.append(asp.fact("fuel_amount", fid, int(f.amount)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if py - ac:
        print("  only in Python:", sorted(py - ac))
    if ac - py:
        print("  only in ASP:", sorted(ac - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale diesel runner with repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--fuel", choices=FUELS)
    ap.add_argument("--name", choices=CHARACTER_NAMES)
    ap.add_argument("--helper", choices=HELPER_TYPES)
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
    combos = valid_combos()
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.vehicle is None or c[1] == args.vehicle)
              and (args.fuel is None or c[2] == args.fuel)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, vehicle, fuel = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHARACTER_NAMES)
    helper = args.helper or rng.choice(HELPER_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, vehicle=vehicle, fuel=fuel, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], VEHICLES[params.vehicle], FUELS[params.fuel],
                 params.name, params.helper, params.trait)
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
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  route_remaining={world.route_remaining}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest_road", vehicle="diesel_wagon", fuel="diesel_can", name="Lina", helper="miller", trait="brave"),
    StoryParams(place="hill_road", vehicle="diesel_wagon", fuel="diesel_can", name="Milo", helper="queen", trait="cheerful"),
    StoryParams(place="castle_lane", vehicle="diesel_wagon", fuel="diesel_can", name="Nora", helper="father", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible combos:\n")
        for place, vehicle, fuel in models:
            print(f"  {place:12} {vehicle:15} {fuel}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.vehicle} / {p.fuel}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
