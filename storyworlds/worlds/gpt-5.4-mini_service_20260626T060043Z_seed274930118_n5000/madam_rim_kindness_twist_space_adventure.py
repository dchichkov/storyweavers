#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure tale about a madam,
a rim, kindness, and a twist.

The story world is intentionally narrow: a captain (often called madam),
a ship or station with a physical rim, a helpful kindness choice, and a
turning twist that resolves the danger.
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
# Core world types
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
        if self.type in {"woman", "madam", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "sir", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    id: str
    label: str
    detail: str
    has_rim: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    place: str
    helps_with: set[str] = field(default_factory=set)
    twist_required: bool = False


@dataclass
class StoryParams:
    place: str
    object: str
    hero_name: str
    hero_type: str
    helper_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "orbital_rim": Location(
        id="orbital_rim",
        label="the orbital rim",
        detail="A bright station curved around the planet like a silver ring.",
        has_rim=True,
        affords={"walk", "repair", "signal"},
    ),
    "moon_dock": Location(
        id="moon_dock",
        label="the moon dock",
        detail="The moon dock sat quiet under a wide black sky.",
        has_rim=True,
        affords={"walk", "repair"},
    ),
    "star_hangar": Location(
        id="star_hangar",
        label="the star hangar",
        detail="The star hangar glowed with blinking lights and polished floors.",
        has_rim=False,
        affords={"repair", "signal"},
    ),
}

OBJECTS = {
    "glass_beacon": ObjectDef(
        id="glass_beacon",
        label="glass beacon",
        phrase="a small glass beacon",
        place="orbital_rim",
        helps_with={"signal"},
        twist_required=True,
    ),
    "tool_satchel": ObjectDef(
        id="tool_satchel",
        label="tool satchel",
        phrase="a sturdy tool satchel",
        place="moon_dock",
        helps_with={"repair"},
        twist_required=False,
    ),
    "moon_map": ObjectDef(
        id="moon_map",
        label="moon map",
        phrase="a folded moon map",
        place="star_hangar",
        helps_with={"walk", "signal"},
        twist_required=False,
    ),
}

HERO_NAMES = ["Mina", "Tala", "Nia", "Rosa", "Lena", "Mira"]
HELPER_NAMES = ["Oren", "Pax", "Ivo", "Suri", "Jori"]
HERO_TYPES = ["woman", "girl", "captain"]

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_combo(location: Location, obj: ObjectDef) -> bool:
    return location.has_rim and obj.twist_required and "signal" in location.affords and "signal" in obj.helps_with


def explain_rejection(place: str, object_id: str) -> str:
    loc = LOCATIONS[place]
    obj = OBJECTS[object_id]
    return (
        f"(No story: {obj.label} needs a real rim twist to matter, but "
        f"{loc.label} does not support the kind of turning problem this tale needs.)"
    )


def choose_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str]:
    combos = []
    for pid, loc in LOCATIONS.items():
        for oid, obj in OBJECTS.items():
            if valid_combo(loc, obj):
                if args.place and args.place != pid:
                    continue
                if args.object and args.object != oid:
                    continue
                combos.append((pid, oid))
    if not combos:
        raise StoryError("(No valid story combination matches the given options.)")
    return rng.choice(sorted(combos))


def build_world(params: StoryParams) -> World:
    location = LOCATIONS[params.place]
    obj = OBJECTS[params.object]

    world = World(location)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="helper"))
    thing = world.add(Entity(
        id=obj.id,
        kind="thing",
        type="object",
        label=obj.label,
        phrase=obj.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))

    hero.meters["hope"] = 1
    hero.memes["kindness"] = 0
    hero.memes["worry"] = 0
    helper.memes["trust"] = 0

    # Act 1: setup
    world.say(
        f"Madam {hero.id} stood at {location.label}, where {location.detail}"
    )
    world.say(
        f"She carried {thing.phrase} and watched the curved rim where the stars seemed close enough to touch."
    )

    # Act 2: tension
    world.para()
    world.say(
        f"Then the ship gave a small shiver, and the beacon's light blinked out."
    )
    hero.memes["worry"] += 1
    world.say(
        f"Madam {hero.id} wanted to call for help, but the signal panel sat too near the rim to fix quickly."
    )

    # Kindness beat
    world.say(
        f"{helper.id} saw her face and chose kindness over hurry."
    )
    hero.memes["kindness"] += 1
    helper.memes["kindness"] = 1

    # Twist
    world.para()
    if obj.twist_required and location.has_rim:
        world.say(
            f"At the rim, the tiny glass beacon had not broken at all; it only needed to be turned a quarter twist."
        )
        world.say(
            f"Madam {hero.id} set {thing.it()} into the panel, turned it just so, and the light came back with a warm blue glow."
        )
        hero.meters["success"] = 1
        helper.memes["trust"] += 1
    else:
        raise StoryError(explain_rejection(params.place, params.object))

    # Resolution
    world.para()
    world.say(
        f"The station hummed again, and Madam {hero.id} smiled as the rim shone beside the returning signal."
    )
    world.say(
        f"Because of kindness and a clever twist, the little beacon helped the whole ship feel safe once more."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        object=thing,
        location=location,
        object_def=obj,
        twist=True,
        kindness=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    obj: Entity = f["object"]  # type: ignore[assignment]
    location: Location = f["location"]  # type: ignore[assignment]
    return [
        f'Write a short space adventure for a child that includes "madam", "kindness", and a "twist".',
        f"Tell a gentle story where Madam {hero.id} fixes {obj.phrase} at {location.label} by being kind and noticing a twist.",
        f"Write a small star-ship tale about a rim, a blinking light, and a helpful turning trick.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    obj: Entity = f["object"]  # type: ignore[assignment]
    location: Location = f["location"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the madam in the story?",
            answer=f"Madam {hero.id} was the captain-like heroine of the space adventure.",
        ),
        QAItem(
            question=f"What problem happened at {location.label}?",
            answer=f"The beacon went dark near the rim, so the ship lost its signal for a moment.",
        ),
        QAItem(
            question=f"What did kindness change in the story?",
            answer=f"Kindness changed the mood of the moment because {helper.id} stayed calm and helped instead of panicking.",
        ),
        QAItem(
            question=f"What was the twist with {obj.label}?",
            answer=f"The twist was that {obj.phrase} was not broken; it only needed a careful quarter turn.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rim?",
            answer="A rim is the outer edge of something round, like a wheel, a cup, or a space station ring.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, being gentle, and caring about how someone else feels.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a turning motion that changes how something is facing or locked in place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id} ({ent.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
location(L) :- loc(L).
object(O) :- obj(O).
rim_place(L) :- has_rim(L).

compatible(L, O) :- has_rim(L), obj(O), needs_twist(O), helps_signal(O), signal_place(L).
valid_story(L, O) :- compatible(L, O).

#show valid_story/2.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("loc", lid))
        if loc.has_rim:
            lines.append(asp.fact("has_rim", lid))
        if "signal" in loc.affords:
            lines.append(asp.fact("signal_place", lid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("obj", oid))
        if obj.twist_required:
            lines.append(asp.fact("needs_twist", oid))
        if "signal" in obj.helps_with:
            lines.append(asp.fact("helps_signal", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(lid, oid) for lid, loc in LOCATIONS.items() for oid, obj in OBJECTS.items() if valid_combo(loc, obj)}
    asp_set = set(asp_valid_combos())
    if asp_set == python_set:
        print(f"OK: clingo gate matches valid_combo() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" only in clingo:", sorted(asp_set - python_set))
    print(" only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld: madam, rim, kindness, and a twist.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
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
    place, object_id = choose_combo(args, rng)
    if args.place and args.object:
        loc = LOCATIONS[args.place]
        obj = OBJECTS[args.object]
        if not valid_combo(loc, obj):
            raise StoryError(explain_rejection(args.place, args.object))
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    return StoryParams(
        place=place,
        object=object_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
    )


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
    StoryParams(place="orbital_rim", object="glass_beacon", hero_name="Mina", hero_type="captain", helper_name="Oren"),
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
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
