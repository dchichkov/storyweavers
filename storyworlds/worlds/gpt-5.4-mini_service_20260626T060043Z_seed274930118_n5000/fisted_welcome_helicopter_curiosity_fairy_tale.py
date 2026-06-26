#!/usr/bin/env python3
"""
storyworlds/worlds/fisted_welcome_helicopter_curiosity_fairy_tale.py
====================================================================

A small fairy-tale storyworld about a curious child, a welcome, and a tiny
helicopter arriving in a gentle enchanted place.

The seed-image behind the domain:
- Someone with Curiosity hears a whirring in the sky.
- A helicopter appears where a storybook village does not expect it.
- Hands fisted in worry, the child learns to welcome the stranger safely.
- The ending proves the welcome changed the world: fear becomes a shared smile.

This script keeps the world small and constraint-checked.
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
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        if self.type in {"girl", "princess", "queen", "fairy"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "prince", "king", "knight"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]


@dataclass
class Place:
    id: str
    label: str
    landing: bool
    curious_about: set[str] = field(default_factory=set)


@dataclass
class Helicopter:
    id: str
    label: str
    phrase: str
    can_land: set[str] = field(default_factory=set)
    can_welcome: bool = True


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    companion: str
    helicopter: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


SETTINGS = {
    "meadow": Place(id="meadow", label="the meadow", landing=True, curious_about={"helicopter"}),
    "castle_garden": Place(id="castle_garden", label="the castle garden", landing=True, curious_about={"helicopter"}),
    "village_square": Place(id="village_square", label="the village square", landing=False, curious_about={"helicopter"}),
    "moon_bridge": Place(id="moon_bridge", label="the moon bridge", landing=True, curious_about={"helicopter"}),
}

HELICOPTERS = {
    "tiny_helicopter": Helicopter(
        id="tiny_helicopter",
        label="a tiny helicopter",
        phrase="a tiny helicopter with a silver bell",
        can_land={"meadow", "castle_garden", "moon_bridge"},
    ),
    "golden_helicopter": Helicopter(
        id="golden_helicopter",
        label="a golden helicopter",
        phrase="a golden helicopter with bright round windows",
        can_land={"castle_garden", "moon_bridge"},
    ),
}

HERO_TYPES = ["girl", "boy", "princess", "prince", "fairy"]
HERO_NAMES = {
    "girl": ["Lina", "Mira", "Nora", "Elsa"],
    "boy": ["Tobin", "Oren", "Pax", "Milo"],
    "princess": ["Princess Elin", "Princess Rosa"],
    "prince": ["Prince Alder", "Prince Rowan"],
    "fairy": ["Faye", "Iris", "Luma"],
}
COMPANIONS = ["grandmother", "father", "mother", "old gardener", "river sprite"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place_id, place in SETTINGS.items():
        if not place.landing:
            continue
        for heli_id, heli in HELICOPTERS.items():
            if place_id in heli.can_land:
                out.append((place_id, heli_id))
    return out


def explain_rejection(place_id: str, heli_id: str) -> str:
    place = SETTINGS[place_id]
    heli = HELICOPTERS[heli_id]
    return (
        f"(No story: {heli.label} cannot safely land at {place.label}. "
        f"Choose a place with a soft landing spot.)"
    )


def build_world(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    heli = HELICOPTERS[params.helicopter]
    world = World(place)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=params.hero_type,
        label=params.hero,
        meters={"curiosity": 0.0, "safety": 0.0},
        memes={"curiosity": 1.0},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=params.companion,
        label=f"the {params.companion}",
        meters={"worry": 0.0, "warmth": 0.0},
        memes={"worry": 0.0},
    ))
    helicopter = world.add(Entity(
        id=heli.id,
        kind="thing",
        type="helicopter",
        label=heli.label,
        phrase=heli.phrase,
        owner=None,
        caretaker=None,
        meters={"wind": 0.0, "rest": 0.0},
        memes={"fear": 0.0, "welcome": 0.0},
    ))

    # Act 1: the curious noticing.
    world.say(
        f"In {place.label}, {hero.id} was a curious little {params.hero_type} who loved to listen to the wind."
    )
    world.say(
        f"One bright morning, {hero.id} heard a soft whirr over the grass and saw {helicopter.phrase}."
    )
    hero.meters["curiosity"] += 1.0
    helicopter.meters["wind"] += 1.0

    # Act 2: tension.
    world.para()
    world.say(
        f"{hero.id} came close, and {hero.pronoun().capitalize()} fisted {hero.pronoun('possessive')} hands when the blades turned."
    )
    companion.meters["worry"] += 1.0
    companion.memes["worry"] += 1.0
    world.say(
        f"The {params.companion} hurried over and said, \"Stay calm; we can welcome the little flyer the safe way.\""
    )
    helicopter.memes["fear"] += 1.0

    # Act 3: welcome and safe landing.
    world.para()
    hero.meters["safety"] += 1.0
    helicopter.meters["rest"] += 1.0
    helicopter.memes["welcome"] += 1.0
    companion.meters["warmth"] += 1.0
    world.say(
        f"{hero.id} waved both hands, and the garden grew quiet enough for {helicopter.label} to settle down."
    )
    world.say(
        f"Then {hero.id} and the {params.companion} welcomed {helicopter.label} like an honored guest."
    )
    world.say(
        f"The whirring stopped, the grass stayed unhurt, and {hero.id} smiled as if the sky itself had come to visit."
    )

    world.facts.update(
        hero=hero,
        companion=companion,
        helicopter=helicopter,
        place=place,
        params=params,
        landed=True,
        welcomed=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    heli = f["helicopter"]
    return [
        f'Write a short fairy tale for a small child about Curiosity, a welcome, and {heli.label}.',
        f"Tell a gentle story where {hero.id} hears {heli.phrase} in {place.label} and learns to welcome it safely.",
        f'Write a simple fairy-tale story that uses the words "fisted", "welcome", and "helicopter".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    heli = f["helicopter"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was curious in {place.label} when {heli.label} arrived?",
            answer=f"{hero.id} was the curious child in {place.label}. {hero.id} listened to the wind and noticed {heli.label}.",
        ),
        QAItem(
            question=f"Why did {hero.id} fisted {hero.pronoun('possessive')} hands at first?",
            answer=(
                f"{hero.id} fisted {hero.pronoun('possessive')} hands because the spinning blades felt startling at first. "
                f"Then the {companion.type} showed a safer way to meet the visitor."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} and the {companion.type} do at the end?",
            answer=(
                f"They welcomed {heli.label} as a guest, let it settle safely, and smiled together when the garden stayed calm."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "curiosity": (
        "What is curiosity?",
        "Curiosity is the feeling that makes you want to look, ask, and learn about something new.",
    ),
    "helicopter": (
        "What is a helicopter?",
        "A helicopter is a flying machine with spinning blades that can lift off and land in special places.",
    ),
    "welcome": (
        "What does it mean to welcome someone?",
        "To welcome someone means to greet them kindly and help them feel safe and wanted.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:18} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- landing_place(P).
helicopter(H) :- can_land(H, P), landing_place(P).
valid_story(P, H) :- landing_place(P), can_land(H, P).
welcomed(P, H) :- valid_story(P, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.landing:
            lines.append(asp.fact("landing_place", pid))
    for hid, heli in HELICOPTERS.items():
        lines.append(asp.fact("helicopter_kind", hid))
        for p in sorted(heli.can_land):
            lines.append(asp.fact("can_land", hid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    ap = argparse.ArgumentParser(
        description="Fairy tale storyworld about Curiosity, a welcome, and a helicopter."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--helicopter", choices=HELICOPTERS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
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
    combos = valid_combos()
    if args.place or args.helicopter:
        combos = [
            (p, h) for p, h in combos
            if (args.place is None or p == args.place)
            and (args.helicopter is None or h == args.helicopter)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, heli = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero = args.hero or rng.choice(HERO_NAMES[hero_type])
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(place=place, hero=hero, hero_type=hero_type, companion=companion, helicopter=heli)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place="meadow", hero="Lina", hero_type="girl", companion="mother", helicopter="tiny_helicopter"),
    StoryParams(place="castle_garden", hero="Prince Rowan", hero_type="prince", companion="old gardener", helicopter="golden_helicopter"),
    StoryParams(place="moon_bridge", hero="Faye", hero_type="fairy", companion="river sprite", helicopter="tiny_helicopter"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.hero}: {p.place} with {p.helicopter}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
