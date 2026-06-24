#!/usr/bin/env python3
"""
storyworlds/worlds/metallic_sissie_transformation_bravery_bedtime_story.py
===========================================================================

A small bedtime-story world about a little sissie, a metallic keepsake, a
gentle transformation, and a brave bedtime turn.

Seed words:
- metallic
- sissie

Story instruments:
- Transformation
- Bravery

The premise is simple: a child wants to keep a shiny metallic treasure close at
bedtime, but the object changes in a way that makes sleep feel uncertain. The
story turns when the sissie finds a brave, caring way to transform the object so
it is safe and comforting by the final image.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    safe: bool = False
    metallic: bool = False
    transformed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "sissie", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

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


# ---------------------------------------------------------------------------
# Story content registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    bedtime_image: str


@dataclass
class Treasure:
    label: str
    phrase: str
    shimmer: str
    danger: str
    transformed_phrase: str


@dataclass
class Transformation:
    id: str
    name: str
    method: str
    result: str
    safe_state: str


SETTINGS = {
    "nursery": Setting(place="the nursery", bedtime_image="a moonbeam on the quilt"),
    "bedroom": Setting(place="the bedroom", bedtime_image="a soft lamp by the bed"),
    "attic_room": Setting(place="the little attic room", bedtime_image="a round window with stars"),
}

TREASURES = {
    "metal_star": Treasure(
        label="metal star",
        phrase="a tiny metallic star",
        shimmer="shone like a pocket moon",
        danger="felt too cold and hard to hug at bedtime",
        transformed_phrase="a soft star charm wrapped in cloth",
    ),
    "metal_bell": Treasure(
        label="metal bell",
        phrase="a little metallic bell",
        shimmer="rang with a bright silver note",
        danger="kept jingling whenever the child turned over",
        transformed_phrase="a quiet bell tucked into a felt pouch",
    ),
    "metal_heart": Treasure(
        label="metal heart",
        phrase="a small metallic heart",
        shimmer="glowed with a bright silver shine",
        danger="was too sharp and chilly for sleepy hands",
        transformed_phrase="a smooth heart resting in a ribbon nest",
    ),
}

TRANSFORMATIONS = {
    "wrap": Transformation(
        id="wrap",
        name="Transformation",
        method="wrap it in soft cloth",
        result="became gentle and warm",
        safe_state="safe and cozy",
    ),
    "nest": Transformation(
        id="nest",
        name="Transformation",
        method="set it into a little ribbon nest",
        result="settled down without clinking",
        safe_state="safe and quiet",
    ),
    "pouch": Transformation(
        id="pouch",
        name="Transformation",
        method="tuck it into a felt pouch",
        result="stayed still beside the pillow",
        safe_state="safe and snug",
    ),
}

BRAVERY_BEATS = [
    "Bravery meant telling the truth about the cold, shiny feeling.",
    "Bravery meant asking for help instead of pretending everything was fine.",
    "Bravery meant changing the treasure so bedtime could feel peaceful.",
]

GENTLE_NAMING = [
    "sissie",
    "little sissie",
    "brave sissie",
    "sleepy sissie",
]

NAMES = ["Mara", "Luna", "Tia", "Nia", "Mina", "Sara"]


# ---------------------------------------------------------------------------
# Parser / params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    treasure: str
    transformation: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about metallic transformation and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for t in TREASURES:
            for tr in TRANSFORMATIONS:
                out.append((s, t, tr))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    transformation = args.transformation or rng.choice(list(TRANSFORMATIONS))
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, treasure=treasure, transformation=transformation, name=name)


# ---------------------------------------------------------------------------
# Prose engine
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = World(place=SETTINGS[params.setting].place)
    child = world.add(Entity(id=params.name, kind="character", type="sissie", label=params.name, meters={"sleepy": 0}, memes={"bravery": 0}))
    treasure_cfg = TREASURES[params.treasure]
    trans = TRANSFORMATIONS[params.transformation]
    treasure = world.add(Entity(
        id="treasure",
        type="treasure",
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        owner=child.id,
        metallic=True,
        safe=False,
    ))

    world.say(f"At {SETTINGS[params.setting].place}, {params.name} was a {GENTLE_NAMING[0]} who loved {treasure_cfg.phrase}.")
    world.say(f"{treasure_cfg.phrase.capitalize()} {treasure_cfg.shimmer}, but at bedtime it {treasure_cfg.danger}.")
    world.para()
    world.say(f"When the room grew quiet, {params.name} felt a little unsure.")
    world.say(BRAVERY_BEATS[0])
    world.say(BRAVERY_BEATS[1])
    world.para()
    world.say(f"Then {params.name} used {trans.name} to {trans.method}.")
    world.say(f"The shiny treasure {trans.result}, and the room felt calmer.")
    treasure.transformed = True
    treasure.safe = True
    world.facts.update(child=child, treasure=treasure, trans=trans, setting=SETTINGS[params.setting], treasure_cfg=treasure_cfg)

    story = (
        f"At {SETTINGS[params.setting].place}, {params.name} was a little sissie who loved "
        f"{treasure_cfg.phrase}. {treasure_cfg.phrase.capitalize()} {treasure_cfg.shimmer}, "
        f"but at bedtime it {treasure_cfg.danger}.\n\n"
        f"When the room grew quiet, {params.name} felt a little unsure. "
        f"{BRAVERY_BEATS[0]} {BRAVERY_BEATS[1]}\n\n"
        f"Then {params.name} used {trans.name} to {trans.method}. The shiny treasure "
        f"{trans.result}, and by the end it was {trans.safe_state}. "
        f"{SETTINGS[params.setting].bedtime_image} stayed in the room, and {params.name} "
        f"could close her eyes with a brave little smile."
    )
    # Keep the live world aligned with the story text for trace output.
    world.paragraphs = [[
        f"At {SETTINGS[params.setting].place}, {params.name} was a little sissie who loved {treasure_cfg.phrase}.",
        f"{treasure_cfg.phrase.capitalize()} {treasure_cfg.shimmer}, but at bedtime it {treasure_cfg.danger}.",
    ], [
        f"When the room grew quiet, {params.name} felt a little unsure.",
        BRAVERY_BEATS[0],
        BRAVERY_BEATS[1],
    ], [
        f"Then {params.name} used {trans.name} to {trans.method}.",
        f"The shiny treasure {trans.result}, and by the end it was {trans.safe_state}.",
        f"{SETTINGS[params.setting].bedtime_image} stayed in the room, and {params.name} could close her eyes with a brave little smile.",
    ]]
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    treasure = f["treasure_cfg"]
    trans = f["trans"]
    return [
        f"Write a bedtime story about a little sissie and {treasure.phrase} that needs {trans.name}.",
        f"Tell a gentle story where a child feels brave enough to change a metallic treasure before sleep.",
        f"Make a calm bedtime tale about {treasure.label} being transformed so it can rest near the pillow.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    treasure_cfg: Treasure = f["treasure_cfg"]
    trans: Transformation = f["trans"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about in {setting.place}?",
            answer=f"It was about {child.label}, a little sissie who loved {treasure_cfg.phrase}.",
        ),
        QAItem(
            question=f"What was hard about the {treasure_cfg.label} at bedtime?",
            answer=f"It was hard because {treasure_cfg.phrase} {treasure_cfg.danger}.",
        ),
        QAItem(
            question=f"What did the child do to help the treasure feel safe?",
            answer=f"{child.label} chose {trans.name} and used it to {trans.method}, so the treasure became gentle for bedtime.",
        ),
        QAItem(
            question=f"How did {child.label} show bravery?",
            answer=f"{child.label} showed bravery by speaking up, asking for help, and changing the shiny treasure into a safe bedtime thing.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does metallic mean?",
            answer="Metallic means shiny like metal, with a bright hard look.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a different state or form.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary in a calm, careful way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for p in sample.prompts:
        parts.append(f"- {p}")
    parts.append("== Story Q&A ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("== World Q&A ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} metallic={e.metallic} transformed={e.transformed} safe={e.safe}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(nursery).
setting(bedroom).
setting(attic_room).

treasure(metal_star).
treasure(metal_bell).
treasure(metal_heart).

transformation(wrap).
transformation(nest).
transformation(pouch).

compatible(S, T, TR) :- setting(S), treasure(T), transformation(TR).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    for tr in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - ap))
    print("asp-only:", sorted(ap - py))
    return 1


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(json.dumps(asp_valid_combos(), indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s, t, tr in valid_combos():
            params = StoryParams(setting=s, treasure=t, transformation=tr, name="Mara")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
