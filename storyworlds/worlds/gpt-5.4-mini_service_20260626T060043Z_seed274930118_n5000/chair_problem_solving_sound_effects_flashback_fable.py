#!/usr/bin/env python3
"""
A standalone storyworld: a fable about chair trouble, sound effects, and a
flashback-guided solution.

The seed premise:
A small creature in a simple home has a favorite chair that starts to wobble.
The creature remembers an older lesson, listens to the chair's noises, and
solves the problem with care instead of force.

The story world is intentionally small and classical:
- one setting
- one main problem
- one remembered lesson
- one concrete fix
- a brief moral-like ending image

This file follows the Storyweavers storyworld contract.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Room:
    name: str = "the kitchen"
    light: str = "warm"


@dataclass
class Character:
    name: str
    kind: str
    trait: str
    meme: dict[str, float] = field(default_factory=dict)


@dataclass
class Chair:
    name: str = "the chair"
    material: str = "wood"
    wobble: float = 0.0
    creak: float = 0.0
    fixed: bool = False
    leg_tightness: float = 0.35
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    kind: str
    trait: str
    room: str
    chair_material: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROOMS = {
    "kitchen": Room(name="the kitchen", light="warm"),
    "porch": Room(name="the porch", light="golden"),
    "workshop": Room(name="the workshop", light="dusty"),
}

KINDS = ["fox", "mouse", "rabbit", "crow", "hedgehog"]
TRAITS = ["wise", "patient", "careful", "gentle", "brave"]

MATERIALS = {
    "wood": ("wooden", "wood"),
    "pine": ("pine", "pine"),
    "oak": ("oak", "oak"),
}

NAMES = {
    "fox": ["Fenn", "Mira", "Tavi"],
    "mouse": ["Nim", "Pip", "Moss"],
    "rabbit": ["Luna", "Bram", "Tilly"],
    "crow": ["Corin", "Sable", "Jett"],
    "hedgehog": ["Pebb", "Tansy", "Brio"],
}

# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.hero: Optional[Character] = None
        self.chair = Chair()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        # meters and memes live on the chair as physical/emotional state
        self.chair.meters = {"wobble": 0.0, "fixedness": 0.0}
        self.chair.memes = {"trust": 0.0, "relief": 0.0}

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World(self.room)
        other.hero = Character(
            name=self.hero.name if self.hero else "",
            kind=self.hero.kind if self.hero else "",
            trait=self.hero.trait if self.hero else "",
            meme=dict(self.hero.meme) if self.hero else {},
        )
        other.chair = Chair(
            name=self.chair.name,
            material=self.chair.material,
            wobble=self.chair.wobble,
            creak=self.chair.creak,
            fixed=self.chair.fixed,
            leg_tightness=self.chair.leg_tightness,
            meters=dict(self.chair.meters),
            memes=dict(self.chair.memes),
        )
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Causal logic
# ---------------------------------------------------------------------------
def chair_is_problematic(world: World) -> bool:
    return world.chair.wobble >= 1.0 or world.chair.creak >= 1.0


def listen_to_chair(world: World) -> None:
    if "listen" in world.fired:
        return
    world.fired.add("listen")
    world.chair.creak += 1.0
    world.chair.meters["wobble"] += 0.5
    world.say("The chair gave a small creak: creak, creak, like a frog clearing its throat.")


def flashback(world: World) -> None:
    if "flashback" in world.fired:
        return
    world.fired.add("flashback")
    world.hero.meme["remembered"] = world.hero.meme.get("remembered", 0.0) + 1.0
    world.say(
        f"{world.hero.name} remembered an old lesson: when something wobbles, "
        f"first find the cause, then fix the cause, not just the noise."
    )


def inspect(world: World) -> None:
    if "inspect" in world.fired:
        return
    world.fired.add("inspect")
    world.say(
        f"{world.hero.name} knelt beside the chair and touched each leg in turn. "
        f"One back leg was looser than the others."
    )


def solve(world: World) -> None:
    if "solve" in world.fired:
        return
    world.fired.add("solve")
    if world.chair.leg_tightness < 0.7:
        world.say(
            f"{world.hero.name} fetched a little wrench and turned the loose screw "
            f"until the leg stood firm."
        )
        world.say("Click, twist, snug. The chair stopped shivering.")
        world.chair.fixed = True
        world.chair.wobble = 0.0
        world.chair.creak = 0.0
        world.chair.meters["fixedness"] = 1.0
        world.chair.memes["trust"] = 1.0
        world.chair.memes["relief"] = 1.0
    else:
        raise StoryError("The chair is already too tight to need this solution.")


def conclude(world: World) -> None:
    if "conclude" in world.fired:
        return
    world.fired.add("conclude")
    if world.chair.fixed:
        world.say(
            f"In the end, {world.hero.name} sat down gently, and the chair answered "
            f"with a soft, steady hush. The little home felt wiser for having listened."
        )
    else:
        world.say(
            f"In the end, {world.hero.name} still stood by the chair, but the problem "
            f"had not yet been solved."
        )


def build_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room)
    hero = Character(name=params.name, kind=params.kind, trait=params.trait)
    world.hero = hero
    world.chair.material = params.chair_material
    world.chair.name = "the chair"
    return world


def tell_story(world: World) -> None:
    hero = world.hero
    chair_word = f"{world.chair.material} chair"

    world.say(
        f"Once in {world.room.name}, there lived a {hero.trait} little {hero.kind} "
        f"named {hero.name}."
    )
    world.say(
        f"{hero.name} loved the {chair_word} by the table, because it was the best "
        f"place to rest after work and play."
    )

    world.para()
    world.say(
        f"One afternoon, the chair began to say a funny sound: creak, creak, creak."
    )
    listen_to_chair(world)
    world.chair.wobble += 1.0
    if chair_is_problematic(world):
        world.say(
            f"{hero.name} noticed that the chair did not just sing; it tipped a little "
            f"when anyone sat on it."
        )

    world.para()
    flashback(world)
    inspect(world)
    solve(world)

    world.para()
    conclude(world)
    world.facts.update(
        hero=hero,
        room=world.room,
        chair=world.chair,
        resolved=world.chair.fixed,
        problem=chair_is_problematic(world),
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a short fable about {hero.name} and a chair that makes a strange sound.",
        "Tell a child-friendly story where listening carefully helps solve a chair problem.",
        "Write a little moral tale with a flashback that leads to fixing a chair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    chair = f["chair"]
    return [
        QAItem(
            question=f"What problem did {hero.name} notice with the chair?",
            answer=f"{hero.name} noticed that the {chair.material} chair was wobbling and making a creaky sound.",
        ),
        QAItem(
            question=f"What did {hero.name} remember from the flashback?",
            answer=(
                f"{hero.name} remembered that the best way to solve a problem is to "
                f"find the cause first and then fix that cause."
            ),
        ),
        QAItem(
            question=f"How was the chair fixed?",
            answer=(
                f"{hero.name} found the loose leg and tightened it with a little wrench "
                f"until the chair became steady."
            ),
        ),
        QAItem(
            question=f"What was the ending image of the story?",
            answer=(
                f"In the end, {hero.name} sat down and the chair answered with a soft, "
                f"steady hush instead of a wobble."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a chair do?",
            answer="A chair is a piece of furniture that people or animals can sit on.",
        ),
        QAItem(
            question="What is a creak?",
            answer="A creak is a small squeaky sound that old or loose things can make when they move.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="Why is listening helpful when something seems broken?",
            answer="Listening can give clues about what is wrong, so you can choose the right fix instead of guessing.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    chair = world.chair
    hero = world.hero
    return "\n".join(
        [
            "--- world model state ---",
            f"room={world.room.name}",
            f"hero={hero.name} ({hero.kind}, {hero.trait})",
            f"chair.material={chair.material}",
            f"chair.wobble={chair.wobble}",
            f"chair.creak={chair.creak}",
            f"chair.fixed={chair.fixed}",
            f"chair.meters={chair.meters}",
            f"chair.memes={chair.memes}",
            f"fired={sorted(world.fired)}",
        ]
    )


# ---------------------------------------------------------------------------
# Reasonableness gate and ASP twin
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for kind in KINDS:
            for material in MATERIALS:
                combos.append((room, kind, material))
    return combos


ASP_RULES = r"""
room(Room) :- room_name(Room).
kind(Kind) :- kind_name(Kind).
material(Mat) :- material_name(Mat).

valid(Room, Kind, Mat) :- room(Room), kind(Kind), material(Mat).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for room in ROOMS:
        lines.append(asp.fact("room_name", room))
    for kind in KINDS:
        lines.append(asp.fact("kind_name", kind))
    for material in MATERIALS:
        lines.append(asp.fact("material_name", material))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
@dataclass
class _Args:
    room: Optional[str] = None
    kind: Optional[str] = None
    trait: Optional[str] = None
    material: Optional[str] = None
    name: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False


CURATED = [
    StoryParams(name="Mira", kind="fox", trait="wise", room="kitchen", chair_material="wood"),
    StoryParams(name="Nim", kind="mouse", trait="patient", room="porch", chair_material="oak"),
    StoryParams(name="Tilly", kind="rabbit", trait="gentle", room="workshop", chair_material="pine"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about a chair, a problem, and a careful fix.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--material", choices=list(MATERIALS))
    ap.add_argument("--name")
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
    room = args.room or rng.choice(list(ROOMS))
    kind = args.kind or rng.choice(KINDS)
    trait = args.trait or rng.choice(TRAITS)
    material = args.material or rng.choice(list(MATERIALS))
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES[kind])
    return StoryParams(name=name, kind=kind, trait=trait, room=room, chair_material=material)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid combos:\n")
        for room, kind, material in triples:
            print(f"  {room:10} {kind:10} {material}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.kind} in {p.room} with {p.material} chair"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
