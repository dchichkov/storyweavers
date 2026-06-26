#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pilot_rouge_contact_happy_ending_foreshadowing_humor.py
=================================================================================================

A small space-adventure story world about a pilot, a rouge signal, and first
contact. The story is built from a simulated world with physical meters and
emotional memes. The premise is simple: a careful pilot wants to complete a
delivery flight, but a strange rouge beacon and a surprise contact create a
choice between caution and curiosity. The turn comes when the pilot notices
foreshadowing clues, solves the puzzle with a funny little mistake, and ends
with a happy first meeting.

The domain stays small on purpose:
- one pilot
- one ship
- one destination
- one mysterious rouge object
- one friendly contact event

The prose should feel like a child-friendly space adventure: concrete, causal,
and with a clear ending image that proves what changed.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"pilot", "captain"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    hull: str
    route: str
    destination: str
    cargo: str


@dataclass
class ContactEvent:
    kind: str
    location: str
    signal: str
    reply: str
    is_friendly: bool = True


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.ship)
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    pilot_name: str
    ship_name: str
    destination: str
    cargo: str
    rouge_object: str
    contact_kind: str
    seed: Optional[int] = None


PILOT_NAMES = ["Nova", "Milo", "Tess", "Ari", "Zed", "Luna", "Rin", "Kiko"]
SHIP_NAMES = ["Starling", "Comet Bell", "Pebble Rocket", "Moon Dart"]
DESTINATIONS = [
    ("the moon station", "moon"),
    ("the red canyon moon", "canyon moon"),
    ("the bright ring port", "ring port"),
]
CARGO = [
    ("snack crates", "snacks"),
    ("mail tubes", "mail"),
    ("seed boxes", "seeds"),
]
ROUGE_OBJECTS = [
    ("a rouge beacon", "beacon"),
    ("a rouge scarf", "scarf"),
    ("a rouge paint can", "paint"),
]
CONTACT_KINDS = [
    ("friendly alien", "alien"),
    ("tiny robot", "robot"),
    ("sleepy moon puff", "creature"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for name in PILOT_NAMES:
        lines.append(asp.fact("pilot_name", name))
    for s in SHIP_NAMES:
        lines.append(asp.fact("ship_name", s))
    for dest_id, dest in DESTINATIONS:
        lines.append(asp.fact("destination", dest_id, dest))
    for cargo_id, cargo in CARGO:
        lines.append(asp.fact("cargo", cargo_id, cargo))
    for rouge_id, rouge in ROUGE_OBJECTS:
        lines.append(asp.fact("rouge_object", rouge_id, rouge))
    for c_id, c in CONTACT_KINDS:
        lines.append(asp.fact("contact_kind", c_id, c))
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(Pilot, Ship, Dest, Cargo, Rouge, Contact) :-
    pilot_name(Pilot), ship_name(Ship),
    destination(Dest, _), cargo(Cargo, _),
    rouge_object(Rouge, _), contact_kind(Contact, _).

#show valid_combo/6.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/6."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with a pilot, rouge clue, and first contact.")
    ap.add_argument("--pilot-name", choices=PILOT_NAMES)
    ap.add_argument("--ship-name", choices=SHIP_NAMES)
    ap.add_argument("--destination", choices=[d[0] for d in DESTINATIONS])
    ap.add_argument("--cargo", choices=[c[0] for c in CARGO])
    ap.add_argument("--rouge-object", choices=[r[0] for r in ROUGE_OBJECTS])
    ap.add_argument("--contact-kind", choices=[c[0] for c in CONTACT_KINDS])
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


def valid_combos() -> list[tuple]:
    combos = []
    for pilot in PILOT_NAMES:
        for ship in SHIP_NAMES:
            for dest, _ in DESTINATIONS:
                for cargo, _ in CARGO:
                    for rouge, _ in ROUGE_OBJECTS:
                        for contact, _ in CONTACT_KINDS:
                            combos.append((pilot, ship, dest, cargo, rouge, contact))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if args.pilot_name is None or c[0] == args.pilot_name
              if args.ship_name is None or c[1] == args.ship_name
              if args.destination is None or c[2] == args.destination
              if args.cargo is None or c[3] == args.cargo
              if args.rouge_object is None or c[4] == args.rouge_object
              if args.contact_kind is None or c[5] == args.contact_kind]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    pilot, ship, dest, cargo, rouge, contact = rng.choice(sorted(combos))
    return StoryParams(
        pilot_name=args.pilot_name or pilot,
        ship_name=args.ship_name or ship,
        destination=args.destination or dest,
        cargo=args.cargo or cargo,
        rouge_object=args.rouge_object or rouge,
        contact_kind=args.contact_kind or contact,
    )


def make_world(params: StoryParams) -> World:
    dest_name = dict(DESTINATIONS)[params.destination]
    cargo_name = dict(CARGO)[params.cargo]
    rouge_name = dict(ROUGE_OBJECTS)[params.rouge_object]
    contact_name = dict(CONTACT_KINDS)[params.contact_kind]
    ship = Ship(
        name=params.ship_name,
        hull="shiny blue hull",
        route="quiet orbit route",
        destination=dest_name,
        cargo=cargo_name,
    )
    world = World(ship)
    pilot = world.add(Entity(id="pilot", kind="character", type="pilot", label=params.pilot_name))
    ship_ent = world.add(Entity(id="ship", kind="thing", type="ship", label=params.ship_name))
    beacon = world.add(Entity(id="rouge", kind="thing", type="object", label=rouge_name))
    contact = world.add(Entity(id="contact", kind="character" if contact_name == "alien" else "thing",
                                type=contact_name, label=contact_name))
    world.facts.update(pilot=pilot, ship=ship_ent, beacon=beacon, contact=contact, params=params)
    return world


def predict_contact(world: World, params: StoryParams) -> dict:
    sim = world.copy()
    sim.get("pilot").memes["curiosity"] = 1
    sim.get("rouge").meters["signal"] = 1
    return {"friendly": True, "mixed_up": True}


def tell(world: World) -> None:
    p = world.facts["params"]
    pilot = world.facts["pilot"]
    beacon = world.facts["beacon"]
    contact = world.facts["contact"]

    world.say(
        f"{pilot.label} was the pilot of the {p.ship_name}, and {pilot.label} loved quiet space routes."
    )
    world.say(
        f"One day, the ship carried {world.ship.cargo} toward {world.ship.destination}, with a small rouge clue tucked in the scanner."
    )
    world.say(
        f"{pilot.label} noticed the rouge {beacon.label} blinking once, then twice, as if it wanted attention."
    )
    world.para()
    world.say(
        f"Near a silver moon field, the scanner gave a tiny beep. That was the first hint that a contact might be near."
    )
    world.say(
        f"{pilot.label} slowed the ship, because the beep and the rouge glow felt like a puzzle instead of a warning."
    )
    world.say(
        f"Then {contact.label} drifted out from behind a rock, holding a sign that said hello in bouncy dots."
    )
    world.para()
    world.say(
        f"{pilot.label} laughed, because the so-called rouge danger was only a paint can from the cargo stack that had rolled into the light."
    )
    world.say(
        f"So the pilot set the can upright, waved back, and shared {world.ship.cargo} with the new friend."
    )
    world.say(
        f"By the end of the trip, the ship kept flying steady, the rouge clue had become a joke, and first contact ended with smiles under the stars."
    )


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Who flew the ship in the story?",
            answer=f"The pilot was {p.pilot_name}, who flew the {p.ship_name}.",
        ),
        QAItem(
            question=f"What made the pilot slow down and look more carefully?",
            answer=f"The blinking rouge clue and the scanner beep made {p.pilot_name} slow down and pay attention.",
        ),
        QAItem(
            question=f"What happened when the contact appeared?",
            answer=f"A friendly first contact happened, and the pilot found out the rouge alarm was only a small joke with the cargo.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a pilot do?",
            answer="A pilot steers a ship and watches the route so everyone can travel safely.",
        ),
        QAItem(
            question="What is first contact?",
            answer="First contact is the first time two travelers from different places meet and begin to understand each other.",
        ),
        QAItem(
            question="Why can a blinking signal be important in space?",
            answer="A blinking signal can be important because it may mean there is something nearby that needs attention.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a funny space adventure about a pilot named {p.pilot_name}, a rouge clue, and a friendly contact.",
        f"Tell a child-friendly story where {p.pilot_name} flies the {p.ship_name} and discovers that the rouge signal is not a disaster.",
        "Write a short happy-ending story with foreshadowing, humor, and a surprise first meeting in space.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(parts)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story QA ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world QA ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def valid_story_combos() -> list[tuple]:
    return valid_combos()


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/6."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} valid space-story combos:\n")
        for c in combos[:20]:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, combo in enumerate(valid_combos()[:5]):
            params = StoryParams(
                pilot_name=combo[0],
                ship_name=combo[1],
                destination=combo[2],
                cargo=combo[3],
                rouge_object=combo[4],
                contact_kind=combo[5],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
