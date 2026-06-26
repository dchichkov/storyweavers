#!/usr/bin/env python3
"""
storyworlds/worlds/chant_sparkle_dim_fuel_sound_effects_surprise.py
===================================================================

A small superhero-style story world about a team chant, a dimming sparkle-core,
and a shared fuel canister that helps everyone finish the rescue together.

The seed premise:
A young hero and friends keep a bright rescue gadget alive by sharing fuel.
When the sparkle goes dim, they use a chant, sound effects, and a surprise
helper to turn the night around.

World shape:
- One hero, one small team, one fragile glowing device, one fuel source.
- The device slowly loses sparkle unless it gets fuel.
- A loud chant and comic-book sound effects help the team act together.
- The ending proves the change by showing the gadget bright again and the fuel
  shared fairly.

This script follows the Storyweavers contract:
- standalone stdlib script
- imports shared result containers eagerly
- lazy-imports ASP helper only inside ASP functions
- includes StoryParams, parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "heroine", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "hero", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    can_host: set[str] = field(default_factory=set)


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    sparkle_key: str = "sparkle_dim"
    fuel_key: str = "fuel"
    needs_sharing: bool = False


@dataclass
class Fuel:
    id: str
    label: str
    phrase: str
    units: int = 1
    shareable: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.history: list[str] = []

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
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.history = list(self.history)
        return clone


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    device: str
    fuel: str
    seed: Optional[int] = None


PLACES = {
    "rooftop": Place(id="rooftop", label="the rooftop", indoors=False, can_host={"chant", "sparkle", "fuel"}),
    "lab": Place(id="lab", label="the little lab", indoors=True, can_host={"chant", "sparkle", "fuel"}),
    "alley": Place(id="alley", label="the moonlit alley", indoors=False, can_host={"chant", "sparkle", "fuel"}),
}

HEROES = [
    ("Nova", "girl"),
    ("Bolt", "boy"),
    ("Milo", "boy"),
    ("Aria", "girl"),
]

SIDEKICKS = [
    ("Pip", "boy"),
    ("Juno", "girl"),
    ("Nix", "girl"),
    ("Taz", "boy"),
]

DEVICES = {
    "lantern": Device(id="lantern", label="rescue lantern", phrase="a rescue lantern with a star-shaped lens"),
    "beacon": Device(id="beacon", label="signal beacon", phrase="a signal beacon that blinked like a tiny star"),
    "drone": Device(id="drone", label="glow-drone", phrase="a glow-drone with a spinning light ring"),
}

FUELS = {
    "battery": Fuel(id="battery", label="battery pack", phrase="a small battery pack", units=2, shareable=True),
    "cells": Fuel(id="cells", label="power cells", phrase="a pair of power cells", units=2, shareable=True),
    "canister": Fuel(id="canister", label="fuel canister", phrase="a bright fuel canister", units=3, shareable=True),
}

# The story uses these exact narrative instruments.
SOUND_EFFECTS = [
    "WHIRR",
    "BEEP-BEEP",
    "ZAP",
    "WHOOSH",
    "PING",
]

CHANTS = [
    "Bright team, light dream!",
    "Share the spark, light the dark!",
    "One for all, all for glow!",
]

SURPRISES = [
    "a tiny robot friend rolled out from behind a crate",
    "the sidekick had already saved half a charge in a pocket pouch",
    "the old lamp on the wall was not broken at all, only sleepy",
]

TRAITS = ["brave", "quick", "cheerful", "clever", "steady"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def _hero_name(hero: Entity) -> str:
    return hero.id


def _place_name(place: Place) -> str:
    return place.label


def _sound_line(effect: str) -> str:
    return f"{effect}!"


def _needs_fuel(device: Entity) -> bool:
    return device.meters.get("sparkle_dim", 0.0) >= THRESHOLD and device.meters.get("fuel", 0.0) < 1.0


def _device_can_brighten(world: World) -> bool:
    device = world.get("device")
    return device.meters.get("fuel", 0.0) >= 1.0


def _apply_fuel(world: World, giver: Entity, device: Entity, amount: float) -> None:
    sig = ("fuel", giver.id, device.id, amount)
    if sig in world.fired:
        return
    world.fired.add(sig)
    device.meters["fuel"] = device.meters.get("fuel", 0.0) + amount
    device.meters["sparkle_dim"] = max(0.0, device.meters.get("sparkle_dim", 0.0) - 0.75)
    giver.memes["share"] = giver.memes.get("share", 0.0) + 1.0


def _dim_device(world: World, device: Entity) -> None:
    sig = ("dim", device.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    device.meters["sparkle_dim"] = device.meters.get("sparkle_dim", 0.0) + 1.0


def _chant(world: World, hero: Entity, sidekick: Entity, chant: str) -> None:
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 0.5
    sidekick.memes["courage"] = sidekick.memes.get("courage", 0.0) + 0.5
    world.say(f'{hero.id} and {sidekick.id} shouted, "{chant}"')


def _surprise(world: World, text: str) -> None:
    world.say(text + ".")


def _share_fuel(world: World, hero: Entity, sidekick: Entity, fuel: Entity, device: Entity) -> None:
    if fuel.units <= 0:
        raise StoryError("The fuel is empty, so there is nothing to share.")
    if not fuel.shareable:
        raise StoryError("This fuel cannot be shared in a reasonable superhero story.")
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 1.0
    sidekick.memes["teamwork"] = sidekick.memes.get("teamwork", 0.0) + 1.0
    _apply_fuel(world, hero, device, 1.0)
    _apply_fuel(world, sidekick, device, 1.0)
    fuel.units = max(0, fuel.units - 2)


def _finish_bright(world: World, hero: Entity, sidekick: Entity, device: Entity, fuel: Entity) -> None:
    device.meters["sparkle_dim"] = 0.0
    device.meters["fuel"] = max(device.meters.get("fuel", 0.0), 2.0)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    sidekick.memes["joy"] = sidekick.memes.get("joy", 0.0) + 1.0
    world.say(
        f"Now the {device.label} shone bright again, and {hero.id} and {sidekick.id} "
        f"shared the last of the fuel so the whole rescue team could head home."
    )


# ---------------------------------------------------------------------------
# Plot construction
# ---------------------------------------------------------------------------

def tell(place: Place, hero_name: str, hero_type: str, sidekick_name: str, sidekick_type: str,
         device_cfg: Device, fuel_cfg: Fuel, trait: str) -> World:
    world = World(place)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"courage": 1.0}))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_type, memes={"courage": 1.0}))
    device = world.add(Entity(
        id="device",
        kind="thing",
        type=device_cfg.id,
        label=device_cfg.label,
        phrase=device_cfg.phrase,
        meters={"sparkle_dim": 0.0, "fuel": 0.0},
    ))
    fuel = world.add(Entity(
        id="fuel",
        kind="thing",
        type=fuel_cfg.id,
        label=fuel_cfg.label,
        phrase=fuel_cfg.phrase,
        meters={"fuel": float(fuel_cfg.units)},
    ))

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        device=device,
        fuel=fuel,
        trait=trait,
        place=place,
    )

    # Act 1: setup
    world.say(
        f"In {_place_name(place)}, {hero.id} was a {trait} little {hero.type} hero, "
        f"and {sidekick.id} was always ready to help."
    )
    world.say(
        f"They guarded the {device.label}, because the city relied on {device.phrase} "
        f"to guide lost people home."
    )
    world.say(
        f"{hero.id} checked the {fuel.label} and said it was enough for one more rescue."
    )

    # Act 2: tension
    world.para()
    _dim_device(world, device)
    world.say(f"Then the lights started to fade: the {device.label} went sparkle-dim.")
    world.say(_sound_line(random.choice(SOUND_EFFECTS)))
    world.say(
        f"{hero.id} frowned when the glow turned weak, because without fuel the rescue signal "
        f"could blink out."
    )
    world.say(
        f"At the same time, {sidekick.id} held up the {fuel.label}, but there was not enough to keep it going alone."
    )

    chant = random.choice(CHANTS)
    world.say(
        f"To stay calm, they started a chant together: \"{chant}\""
    )

    # Act 3: surprise + sharing resolution
    world.para()
    surprise = random.choice(SURPRISES)
    _surprise(world, f"Surprise: {surprise}")
    world.say(
        f"That made {hero.id} laugh, and the laugh turned into a plan."
    )

    _share_fuel(world, hero, sidekick, fuel, device)
    world.say(
        f"{hero.id} passed the fuel to {sidekick.id}, and {sidekick.id} passed it back after a careful recharge."
    )
    world.say(_sound_line("WHIRR"))
    world.say(_sound_line("PING"))
    _finish_bright(world, hero, sidekick, device, fuel)

    world.facts["chant"] = chant
    world.facts["surprise"] = surprise
    world.facts["trait"] = trait
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    device = f["device"]
    fuel = f["fuel"]
    trait = f["trait"]
    return [
        f'Write a short superhero story for a child where {hero.id} and {sidekick.id} share {fuel.label} to fix a {device.label}.',
        f'Write a bright, kid-friendly adventure that includes the words "chant", "sparkle-dim", and "fuel".',
        f"Tell a story in which a {trait} hero hears sound effects, gets a surprise, and learns that sharing helps save the day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    device: Entity = f["device"]
    fuel: Entity = f["fuel"]
    trait: str = f["trait"]
    place: Place = f["place"]
    chant: str = f["chant"]
    surprise: str = f["surprise"]

    return [
        QAItem(
            question=f"Who were the two heroes in the story at {_place_name(place)}?",
            answer=f"The story was about {hero.id} and {sidekick.id}, two small heroes who worked together at {_place_name(place)}.",
        ),
        QAItem(
            question=f"What happened to the {device.label} before the team shared the {fuel.label}?",
            answer=f"The {device.label} went sparkle-dim and started to lose its bright rescue glow.",
        ),
        QAItem(
            question=f"What did {hero.id} and {sidekick.id} do after the warning sound effects?",
            answer=f"They used a chant, shared the {fuel.label}, and helped the {device.label} shine bright again.",
        ),
        QAItem(
            question=f"Why did the team need to share fuel instead of using it all at once?",
            answer=f"They needed to share the fuel because the rescue device was running low, and sharing let both heroes help keep it powered.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that {surprise}, which gave the heroes a new idea and helped turn the problem around.",
        ),
        QAItem(
            question=f"How did {trait} {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and happy at the end, because the team shared the fuel and the rescue light came back bright.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "chant": [
        QAItem(
            question="What is a chant?",
            answer="A chant is a repeated line or rhythm that people say together to help them feel brave, focused, or excited.",
        )
    ],
    "sparkle_dim": [
        QAItem(
            question="What does sparkle-dim mean?",
            answer="Sparkle-dim means a light or shine is getting weaker, so it is not as bright as before.",
        )
    ],
    "fuel": [
        QAItem(
            question="What is fuel used for?",
            answer="Fuel is something that gives power so a machine, light, or vehicle can keep going.",
        )
    ],
    "sound_effects": [
        QAItem(
            question="Why do stories use sound effects?",
            answer="Stories use sound effects to make actions feel lively, like a comic book coming to life.",
        )
    ],
    "sharing": [
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing is helpful because it lets more than one person use something and work together.",
        )
    ],
    "surprise": [
        QAItem(
            question="What makes a surprise fun in a story?",
            answer="A surprise is fun in a story when something unexpected happens and helps the characters change what they do next.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *WORLD_KNOWLEDGE["chant"],
        *WORLD_KNOWLEDGE["sparkle_dim"],
        *WORLD_KNOWLEDGE["fuel"],
        *WORLD_KNOWLEDGE["sound_effects"],
        *WORLD_KNOWLEDGE["sharing"],
        *WORLD_KNOWLEDGE["surprise"],
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


# ---------------------------------------------------------------------------
# ASP twin and parity checks
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A device is in trouble when its sparkle is dim and it does not have fuel.
dimmed(D) :- sparkle_dim(D).
needs_fuel(D) :- sparkle_dim(D), not fueled(D).

% Sharing fuel makes the device fueled.
fueled(D) :- shares_fuel(H, S, D).

% A story is reasonable when the place supports chant/surprise/sharing,
% the device can dim, and the fuel is shareable.
valid_story(P, H, S, D, F) :-
    place(P), hero(H), sidekick(S), device(D), fuel(F),
    supports(P, chant), supports(P, surprise), supports(P, sharing),
    can_dim(D), can_share(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for feat in sorted(place.can_host):
            lines.append(asp.fact("supports", pid, feat))
    for hid, _ in HEROES:
        lines.append(asp.fact("hero", hid))
    for sid, _ in SIDEKICKS:
        lines.append(asp.fact("sidekick", sid))
    for did, _ in DEVICES.items():
        lines.append(asp.fact("device", did))
        lines.append(asp.fact("can_dim", did))
    for fid, fuel in FUELS.items():
        lines.append(asp.fact("fuel", fid))
        if fuel.shareable:
            lines.append(asp.fact("can_share", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Compare ASP and Python reasonableness gates.
    python_set = set(valid_combos())
    asp_set = set(asp_valid_stories())
    asp_triplets = {(p, h, s, d, f) for (p, h, s, d, f) in asp_set}
    python_triplets = {(p, h, s, d, f) for (p, h, s, d, f) in python_set}
    if asp_triplets == python_triplets:
        print(f"OK: ASP and Python gates match ({len(python_triplets)} story combos).")
        # also exercise generation
        sample = generate(resolve_params(argparse.Namespace(
            place=None, hero=None, sidekick=None, device=None, fuel=None, seed=123,
            n=1, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False
        ), random.Random(123)))
        if not sample.story.strip():
            print("ERROR: generated story is empty.")
            return 1
        print("OK: generation produced a story.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  only in ASP:", sorted(asp_triplets - python_triplets))
    print("  only in Python:", sorted(python_triplets - asp_triplets))
    return 1


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for place in PLACES:
        for hero, _ in HEROES:
            for sidekick, _ in SIDEKICKS:
                if hero == sidekick:
                    continue
                for device in DEVICES:
                    for fuel in FUELS:
                        combos.append((place, hero, sidekick, device, fuel))
    return combos


# ---------------------------------------------------------------------------
# Resolver / generator
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero story world: chant, sparkle-dim, fuel, sound effects, surprise, sharing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--fuel", choices=FUELS)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.hero:
        combos = [c for c in combos if c[1] == args.hero]
    if args.sidekick:
        combos = [c for c in combos if c[2] == args.sidekick]
    if args.device:
        combos = [c for c in combos if c[3] == args.device]
    if args.fuel:
        combos = [c for c in combos if c[4] == args.fuel]
    if not combos:
        raise StoryError("No valid superhero story matches those choices.")

    place, hero_name, sidekick_name, device_id, fuel_id = rng.choice(sorted(combos))
    hero_type = next(t for n, t in HEROES if n == hero_name)
    sidekick_type = next(t for n, t in SIDEKICKS if n == sidekick_name)
    return StoryParams(
        place=place,
        hero=hero_name,
        sidekick=sidekick_name,
        device=device_id,
        fuel=fuel_id,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    place = PLACES[params.place]
    hero_type = next(t for n, t in HEROES if n == params.hero)
    sidekick_type = next(t for n, t in SIDEKICKS if n == params.sidekick)
    trait = rng.choice(TRAITS)
    world = tell(
        place=place,
        hero_name=params.hero,
        hero_type=hero_type,
        sidekick_name=params.sidekick,
        sidekick_type=sidekick_type,
        device_cfg=DEVICES[params.device],
        fuel_cfg=FUELS[params.fuel],
        trait=trait,
    )
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story tuples:\n")
        for tup in stories:
            print("  ", tup)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="rooftop", hero="Nova", sidekick="Pip", device="lantern", fuel="canister", seed=base_seed),
            StoryParams(place="lab", hero="Aria", sidekick="Nix", device="beacon", fuel="battery", seed=base_seed + 1),
            StoryParams(place="alley", hero="Bolt", sidekick="Taz", device="drone", fuel="cells", seed=base_seed + 2),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
            header = f"### {p.hero} and {p.sidekick} at {p.place} ({p.device} / {p.fuel})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
