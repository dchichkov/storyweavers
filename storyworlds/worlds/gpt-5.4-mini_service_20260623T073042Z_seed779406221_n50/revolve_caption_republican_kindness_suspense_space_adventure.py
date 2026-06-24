#!/usr/bin/env python3
"""
storyworlds/worlds/revolve_caption_republican_kindness_suspense_space_adventure.py
==================================================================================

A small standalone story world for a child-facing Space Adventure style tale
about a ship that must revolve around a plan, a caption that helps everyone
understand, and a republican town-hall crew learning kindness under suspense.

Seed tale imagined from the prompt:
---
On a quiet star route, Captain Rhea piloted the ship Revolve toward a round moon
station. A little robot captioned the map, and a republican council on the
station argued about who should get the last water crate. The ship's crew wanted
to land, but the station's gate stayed closed until someone could be kind enough
to share. Under the suspense of a drifting storm ring, the crew learned that
small helpful actions open bigger doors than loud speeches.

This script builds that premise into a tiny simulation with physical meters
(movement, supplies, door state) and emotional memes (kindness, suspense,
frustration). State drives the prose: the ship arrives, the gate blocks access,
a choice either escalates tension or resolves it, and the ending proves what
changed.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"kindness": 0.0, "suspense": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def display(self) -> str:
        return self.label or self.id


@dataclass
class Ship:
    name: str
    label: str
    realm: str
    meters: dict[str, float] = field(default_factory=lambda: {"revolve": 0.0, "fuel": 0.0, "supply": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"kindness": 0.0, "suspense": 0.0})
    facts: dict = field(default_factory=dict)
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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

    def copy(self) -> "Ship":
        import copy as _copy
        c = Ship(self.name, self.label, self.realm)
        c.meters = _copy.deepcopy(self.meters)
        c.memes = _copy.deepcopy(self.memes)
        c.facts = _copy.deepcopy(self.facts)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        return c


@dataclass
class Station:
    name: str
    kind: str
    label: str
    gate: str
    resource: str
    orbit: str
    demand: str


@dataclass
class CrewPlan:
    id: str
    noun: str
    verb: str
    helpful: str
    turn: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Offer:
    id: str
    label: str
    amount: int
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    station: str
    plan: str
    offer: str
    name: str
    role: str
    companion: str
    seed: Optional[int] = None


STATIONS = {
    "moonport": Station("moonport", "station", "the moon port", "airlock gate", "water crate", "round orbit", "share the last crate"),
    "ringhub": Station("ringhub", "station", "the ring hub", "dock gate", "food crate", "bright orbit", "share the last crate"),
}

PLANS = {
    "revolve": CrewPlan("revolve", "the ship Revolve", "revolve around the station", "circle the station carefully", "keep everyone calm", {"space", "orbit", "revolve"}),
    "dock": CrewPlan("dock", "the ship", "dock at the gate", "land gently", "open the way", {"space", "dock"}),
}

OFFERS = {
    "water": Offer("water", "water", 1, "quench thirst", {"share", "water"}),
    "tools": Offer("tools", "tool box", 1, "fix the gate", {"share", "tools"}),
    "snacks": Offer("snacks", "snacks", 1, "ease the wait", {"share", "food"}),
}

NAMES = ["Mira", "Tess", "Noah", "Luz", "Ari", "Nia"]
COMPANIONS = ["pilot", "captain", "robot", "mechanic"]
ROLES = ["captain", "pilot", "navigator", "mechanic"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, p, o) for s in STATIONS for p in PLANS for o in OFFERS if p == "revolve" or s == "ringhub"]


@dataclass
class World:
    ship: Ship
    station: Station
    plan: CrewPlan
    offer: Offer
    hero: Entity
    companion: Entity
    gate_open: bool = False
    shared: bool = False
    resolved_kindness: bool = False


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in STATIONS:
        lines.append(asp.fact("station", sid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
    for oid in OFFERS:
        lines.append(asp.fact("offer", oid))
    for sid, st in STATIONS.items():
        lines.append(asp.fact("requires_share", sid, st.demand.replace(" ", "_")))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,O) :- station(S), plan(P), offer(O).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure story world about kindness under suspense.")
    ap.add_argument("--station", choices=STATIONS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--offer", choices=OFFERS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--companion", choices=COMPANIONS)
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
    combos = [c for c in valid_combos()
              if (args.station is None or c[0] == args.station)
              and (args.plan is None or c[1] == args.plan)
              and (args.offer is None or c[2] == args.offer)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    station, plan, offer = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(station, plan, offer, name, role, companion)


def tell(params: StoryParams) -> World:
    station = STATIONS[params.station]
    plan = PLANS[params.plan]
    offer = OFFERS[params.offer]
    ship = Ship("Revolve", "the ship Revolve", "space")
    hero = ship.add(Entity(params.name, kind="character", type="captain" if params.role == "captain" else "person", label=params.name, role="hero"))
    companion = ship.add(Entity(params.companion, kind="character", type="person", label=params.companion, role="helper"))
    world = World(ship, station, plan, offer, hero, companion)
    ship.facts = {}
    ship.meters["revolve"] = 1.0 if plan.id == "revolve" else 0.0
    ship.memes["suspense"] = 1.0
    hero.memes["kindness"] = 1.0
    companion.memes["suspense"] = 1.0
    ship.say(f"The {ship.label} drifted through a quiet stretch of space toward {station.label}.")
    ship.say(f"{hero.display} and the {companion.display} watched the blue stars slide by while the ship began to {plan.verb}.")
    ship.para()
    ship.say(f"At {station.label}, the {station.gate} stayed closed because everyone wanted to {station.demand}.")
    ship.say(f"The wait made the cabin feel full of suspense, but {hero.display} noticed the problem was small enough for kindness to solve.")
    if offer.id == "water":
        ship.say(f"{hero.display} offered the water crate first, so the station crew could drink before the next turn through orbit.")
    elif offer.id == "tools":
        ship.say(f"{hero.display} shared the tool box and helped the gate team fix a stuck latch.")
    else:
        ship.say(f"{hero.display} shared the snacks, and the worried crew softened right away.")
    world.shared = True
    world.gate_open = True
    world.resolved_kindness = True
    ship.memes["kindness"] += 1
    ship.memes["suspense"] = 0.0
    ship.para()
    ship.say(f"Then the {station.gate} opened, and the {plan.noun} moved on.")
    ship.say(f"By the end, the ship kept revolving in the bright orbit, and the whole crew felt proud that kindness had opened the way.")
    ship.facts.update(hero=hero, companion=companion, station=station, plan=plan, offer=offer, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.ship.facts
    return [
        f'Write a child-friendly space adventure story that uses the words "revolve", "caption", and "republican".',
        f"Tell a suspenseful but kind space story where {f['hero'].display} helps a station crew by sharing {f['offer'].label}.",
        f"Write a short story for a young child about a ship called Revolve, a closed gate, and a kind choice that opens it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.ship.facts
    return [
        QAItem(question=f"Who helped the station crew in the story?", answer=f"{f['hero'].display} helped by sharing {f['offer'].label}."),
        QAItem(question="What feeling made the waiting tense?", answer="Suspense made the waiting feel tense, because the gate stayed closed until someone shared."),
        QAItem(question="What changed at the end?", answer="The gate opened, the ship moved on, and kindness solved the problem."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does revolve mean?", answer="Revolve means to move around in a circle or orbit."),
        QAItem(question="What is a caption?", answer="A caption is a short line of words that explains a picture, map, or scene."),
        QAItem(question="What is kindness?", answer="Kindness means helping, sharing, and caring about other people."),
        QAItem(question="What is suspense?", answer="Suspense is the feeling of waiting to see what will happen next."),
        QAItem(question="What does a republican council mean here?", answer="Here it means a group of station citizens who make choices together."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.ship.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"ship: meters={dict(world.ship.meters)} memes={dict(world.ship.memes)}")
    lines.append(f"gate_open={world.gate_open} shared={world.shared} resolved_kindness={world.resolved_kindness}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.ship.render(),
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


CURATED = [
    StoryParams("moonport", "revolve", "water", "Rhea", "captain", "pilot"),
    StoryParams("ringhub", "dock", "snacks", "Mina", "navigator", "robot"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
