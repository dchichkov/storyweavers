#!/usr/bin/env python3
"""
Croissant adventure storyworld with dialogue and a happy ending.

A child gets a treasured croissant for a little adventure, but the journey
threatens to crush or smudge it. The world model tracks the croissant's
physical state and the child's feelings, and the story resolves when a
protective plan keeps the pastry safe.
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
# Typed world model
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
    contained_in: Optional[str] = None
    protected: bool = False
    meters: dict[str, float] = field(default_factory=dict)  # physical
    memes: dict[str, float] = field(default_factory=dict)  # emotional

    def __post_init__(self) -> None:
        for k in ["crushed", "buttered", "stale", "safe"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "hope", "relief", "bravery"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool
    wind: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Transport:
    id: str
    label: str
    protects: set[str]
    hold: str
    offer: str
    action: str


@dataclass
class StoryParams:
    place: str
    transport: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path_wind = place.wind
        self.story_started = False

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
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.path_wind = self.path_wind
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "bakery": Place(name="the bakery", indoors=True, wind=False, affords={"shop", "pack"}),
    "trail": Place(name="the hill trail", indoors=False, wind=True, affords={"walk", "climb"}),
    "park": Place(name="the park", indoors=False, wind=True, affords={"walk", "picnic"}),
}

TRANSPORTS = {
    "paper_bag": Transport(
        id="paper_bag",
        label="a paper bag",
        protects={"crumbs"},
        hold="carry the croissant in a paper bag",
        offer="put it in a paper bag",
        action="held the bag very carefully",
    ),
    "tin_box": Transport(
        id="tin_box",
        label="a tin box",
        protects={"crushed", "crumbs", "stale"},
        hold="carry the croissant in a tin box",
        offer="put it in a tin box",
        action="closed the tin box with a soft click",
    ),
    "napkin_wrap": Transport(
        id="napkin_wrap",
        label="a clean napkin wrap",
        protects={"crumbs", "buttered"},
        hold="wrap the croissant in a clean napkin",
        offer="wrap it in a clean napkin",
        action="tucked the napkin around it",
    ),
}

CHILD_NAMES = ["Mila", "Noah", "Zoe", "Eli", "Ava", "Leo"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]
GENDERS = ["girl", "boy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A croissant is at risk when a place is windy or the chosen carry method does
% not protect it from crushing and crumbs.
risk(P, T) :- place(P), transport(T), windy(P), not safe_for(T, crushed).
risk(P, T) :- place(P), transport(T), windy(P), not safe_for(T, crumbs).

valid(P, T) :- place(P), transport(T), risk(P, T), safe_for(T, crushed), safe_for(T, crumbs).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.wind:
            lines.append(asp.fact("windy", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, tr in TRANSPORTS.items():
        lines.append(asp.fact("transport", tid))
        for s in sorted(tr.protects):
            lines.append(asp.fact("safe_for", tid, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def needs_protection(place: Place, transport: Transport) -> bool:
    return place.wind and "crushed" in transport.protects


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for pid, place in PLACES.items():
        for tid, tr in TRANSPORTS.items():
            if place.indoors:
                if "crushed" in tr.protects or "crumbs" in tr.protects:
                    out.append((pid, tid))
            else:
                if needs_protection(place, tr):
                    out.append((pid, tid))
    return out


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def update_risk(world: World, croissant: Entity) -> None:
    if world.place.wind and croissant.contained_in is None:
        croissant.meters["crumbs"] += 1
        croissant.meters["crushed"] += 1


def apply_walk(world: World, hero: Entity, croissant: Entity) -> None:
    hero.memes["joy"] += 1
    if world.place.wind:
        if croissant.contained_in is None:
            croissant.meters["crushed"] += 1
            croissant.meters["crumbs"] += 1
            hero.memes["worry"] += 1
        else:
            croissant.meters["safe"] += 1


def predict(world: World, hero: Entity, croissant: Entity, transport: Transport) -> bool:
    sim = world.copy()
    c = sim.get(croissant.id)
    c.contained_in = transport.id
    apply_walk(sim, sim.get(hero.id), c)
    return c.meters["crushed"] >= THRESHOLD


def tell_world(place: Place, transport: Transport, name: str, gender: str, helper: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    grownup = world.add(Entity(id="Helper", kind="character", type=helper, label=helper))
    croissant = world.add(
        Entity(
            id="croissant",
            type="croissant",
            label="croissant",
            phrase="a golden croissant",
            owner=hero.id,
            caretaker=grownup.id,
        )
    )

    hero.memes["hope"] += 1
    world.say(f"{hero.id} was a little {gender} who loved adventures with breakfast treats.")
    world.say(f"One morning, {hero.id}'s {helper} bought {hero.pronoun('object')} {croissant.phrase}.")
    world.say(f"{hero.id} grinned. \"Can we take it on our adventure?\" {hero.pronoun()} asked.")
    world.para()

    world.say(
        f"They went to {place.name}, where the air felt { 'breezy' if place.wind else 'quiet' } and the path looked ready for a little quest."
    )
    world.say(f"\"Will the croissant be okay?\" {hero.pronoun()} asked.")
    world.say(f"\"Only if we {transport.offer},\" {helper} said.")
    world.say(f"\"Then let's do that,\" {hero.pronoun()} said.")
    croissant.contained_in = transport.id
    world.say(f"{helper.capitalize()} {transport.action}.")
    world.para()

    apply_walk(world, hero, croissant)
    if croissant.contained_in is not None:
        croissant.meters["safe"] += 1

    if world.place.wind and transport.id != "tin_box":
        hero.memes["worry"] += 1
        world.say(f"The wind tugged at the bag, and {hero.id} held it close. \"Careful,\" {helper} said.")
        if predict(world, hero, croissant, transport):
            # should not happen for valid combos
            raise StoryError("The chosen transport did not actually keep the croissant safe.")
    else:
        world.say(f"The croissant stayed snug and warm, as if it knew the trip was meant for it.")

    world.para()
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(f'At the end of the trail, {hero.id} opened the container and said, "It still looks perfect!"')
    world.say(f'\"Then our little adventure was a success,\" {helper} said, smiling.')
    world.say(
        f"{hero.id} took one happy bite, and the croissant stayed neat and golden in the story of the day."
    )

    world.facts.update(
        hero=hero,
        helper=grownup,
        croissant=croissant,
        transport=transport,
        place=place,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    transport = f["transport"]
    place = f["place"]
    return [
        f'Write a short adventure story for a small child that includes the word "croissant" and a happy ending.',
        f'Write a dialogue-filled story about {hero.id} taking a croissant to {place.name} and keeping it safe using {transport.label}.',
        f'Write a gentle adventure where a child asks, "Can we take the croissant?" and the grown-up helps with a safe plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    croissant = f["croissant"]
    transport = f["transport"]
    place = f["place"]

    return [
        QAItem(
            question=f"What did {hero.id} want to take on the adventure?",
            answer=f"{hero.id} wanted to take the croissant on the adventure.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s {helper.label} suggest using {transport.label}?",
            answer=f"{helper.label.capitalize()} suggested {transport.label} so the croissant would stay safe on the trip to {place.name}.",
        ),
        QAItem(
            question=f"What made the trip feel risky at {place.name}?",
            answer=f"The wind at {place.name} could crush or scatter the croissant if it was not protected.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily with {hero.id} taking a bite of the croissant after it stayed safe and neat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a croissant?",
            answer="A croissant is a flaky, buttery pastry that is often shaped like a crescent.",
        ),
        QAItem(
            question="Why do people use a tin box for pastries?",
            answer="People use a tin box to protect pastries from being crushed and to help them stay fresh on the way.",
        ),
        QAItem(
            question="What does wind do on a path?",
            answer="Wind can tug at light things, like paper or napkins, and make carrying them more tricky.",
        ),
    ]


# ---------------------------------------------------------------------------
# Params and CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Croissant adventure storyworld with dialogue and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--transport", choices=TRANSPORTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    if args.place or args.transport:
        combos = [
            (p, t)
            for p, t in combos
            if (args.place is None or p == args.place)
            and (args.transport is None or t == args.transport)
        ]
    if not combos:
        raise StoryError("No valid adventure combination matches those options.")

    place, transport = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, transport=transport, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell_world(PLACES[params.place], TRANSPORTS[params.transport], params.name, params.gender, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.contained_in:
            bits.append(f"contained_in={e.contained_in}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid adventure combos:")
        for p, t in combos:
            print(f"  {p:8} {t:12}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p, t in sorted(valid_combos()):
            params = StoryParams(
                place=p,
                transport=t,
                name=CHILD_NAMES[0],
                gender="girl",
                helper=HELPERS[0],
                seed=base_seed,
            )
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
