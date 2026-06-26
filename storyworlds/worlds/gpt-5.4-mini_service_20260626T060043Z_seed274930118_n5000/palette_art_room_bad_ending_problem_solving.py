#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/palette_art_room_bad_ending_problem_solving.py
=========================================================================================================================

A small comedy storyworld set in an art room, built around a palette, a bad
ending, a problem-solving turn, and a happy ending.

Premise:
- A child loves painting with a favorite palette in an art room.

Tension:
- The palette gets mixed up, the colors turn muddy, and the first attempt to
  fix it goes wrong.

Turn:
- The child notices the mistake, separates the paints, and cleans the palette.

Resolution:
- A clever, practical solution restores the colors and ends with a bright,
  funny, happy image.

This script follows the Storyweavers contract:
- self-contained stdlib storyworld script
- shared result containers imported eagerly
- ASP twin with inline rules and fact emission
- reasonableness gate plus verification
- story-driven world state with meters and memes
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

SETTINGS = {
    "art_room": {
        "place": "the art room",
        "kind": "art_room",
        "affords": {"painting", "mixing", "cleaning"},
    }
}

PALETTES = {
    "wooden_palette": {
        "label": "wooden palette",
        "phrase": "a smooth wooden palette",
        "material": "wood",
    },
    "white_palette": {
        "label": "white palette",
        "phrase": "a bright white palette",
        "material": "plastic",
    },
}

PAINTS = {
    "red": {"label": "red paint", "color": "red"},
    "blue": {"label": "blue paint", "color": "blue"},
    "yellow": {"label": "yellow paint", "color": "yellow"},
    "green": {"label": "green paint", "color": "green"},
}

TOOLS = {
    "brush": {"label": "paintbrush", "plural": False},
    "rag": {"label": "soft rag", "plural": False},
    "water_cup": {"label": "cup of water", "plural": False},
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Ivy", "Tess", "Maya"]
BOY_NAMES = ["Finn", "Theo", "Max", "Leo", "Ben", "Owen"]
TRAITS = ["curious", "cheerful", "silly", "playful", "careful"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "mother"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "father"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    palette: str
    child_name: str
    gender: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: dict) -> None:
        self.setting = setting
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: palette trouble in an art room.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--palette", choices=PALETTES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or "art_room"
    palette = args.palette or rng.choice(list(PALETTES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, palette=palette, child_name=name, gender=gender, trait=trait)


def _character_label(params: StoryParams) -> str:
    return f"{params.trait} {params.gender}"


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.child_name))
    palette_cfg = PALETTES[params.palette]
    palette = world.add(Entity(
        id="palette",
        type="palette",
        label=palette_cfg["label"],
        phrase=palette_cfg["phrase"],
        owner=child.id,
        meters={"mess": 0.0, "clean": 1.0, "mixed_up": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "embarrassment": 0.0, "relief": 0.0},
    ))
    brush = world.add(Entity(id="brush", type="brush", label="paintbrush", owner=child.id))
    rag = world.add(Entity(id="rag", type="rag", label="soft rag", owner=child.id))
    water = world.add(Entity(id="water", type="water_cup", label="cup of water", owner=child.id))

    # Setup
    world.say(
        f"{child.id} was a {params.trait} {params.gender} who loved painting in {world.setting['place']}."
    )
    world.say(
        f"{child.id} had {palette.phrase} and liked lining up the colors just so."
    )
    world.say(
        f"One afternoon, {child.id} chose {brush.label}, {rag.label}, and {water.label} for a fresh painting adventure."
    )

    # Bad ending / problem begins.
    world.para()
    world.say(
        f"{child.id} tried to make the palette look extra fancy by tipping every paint into one tiny corner."
    )
    palette.meters["mixed_up"] += 1.0
    palette.meters["mess"] += 1.0
    palette.memes["worry"] += 1.0
    world.say(
        f"Red met blue, blue met yellow, and the whole palette turned into a grumpy brown puddle."
    )
    world.say(
        f"{child.id} stared at it and sighed, because now the colors looked like muddy soup."
    )
    world.say(
        f"That was the bad ending for the first try: the painting plan had become a comedy of tiny stains."
    )

    # Problem solving turn.
    world.para()
    world.say(
        f"Then {child.id} blinked, laughed at the mess, and said, \"Oops, that palette needs a rescue mission.\""
    )
    world.say(
        f"{child.id} used {rag.label} to wipe the rim, poured fresh water into the cup, and scraped the colors apart."
    )
    palette.meters["mixed_up"] = 0.0
    palette.meters["mess"] = 0.0
    palette.meters["clean"] = 1.0
    palette.memes["worry"] = 0.0
    palette.memes["relief"] += 1.0
    world.say(
        f"With a careful little grin, {child.id} put each color back in its own space so the palette could breathe again."
    )

    # Happy ending.
    world.para()
    child.memes["joy"] = child.memes.get("joy", 0.0) + 2.0
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    world.say(
        f"At last, {child.id} dipped the brush into a bright red spot and painted a smiling cat with a bow tie."
    )
    world.say(
        f"The palette stayed neat, the colors shone, and {child.id} laughed at the funny little rescue."
    )
    world.say(
        f"By the end, {child.id} had a clean palette, a happy picture, and a story that started messy and ended bright."
    )

    world.facts.update(
        child=child,
        palette=palette,
        brush=brush,
        rag=rag,
        water=water,
        params=params,
        ruined=True,
        fixed=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    params = f["params"]
    return [
        f'Write a funny story for a small child about a {params.trait} {params.gender} in an art room with a palette.',
        f"Tell a comedy story where {child.id} makes a palette mess, solves the problem, and ends happily.",
        f"Write a short story with a bad ending, a problem-solving turn, and a happy ending about a palette.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    palette = f["palette"]
    params = f["params"]
    return [
        QAItem(
            question=f"What did {child.id} love to use in the art room?",
            answer=f"{child.id} loved using {palette.phrase} in the art room.",
        ),
        QAItem(
            question=f"What went wrong when {child.id} tried to be extra fancy with the colors?",
            answer="The colors got mixed together into a muddy brown puddle, and the palette became messy.",
        ),
        QAItem(
            question=f"How did {child.id} fix the problem?",
            answer=f"{child.id} wiped the palette with a rag, used water, and separated the colors again.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"It ended happily, with {child.id} painting a cheerful picture and the palette staying clean.",
        ),
        QAItem(
            question=f"What kind of story was this about {params.child_name}?",
            answer="It was a comedy story with a bad ending first, then problem solving, and finally a happy ending.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a palette used for?",
            answer="A palette is a flat surface where you can hold and mix paint colors while you paint.",
        ),
        QAItem(
            question="Why do artists clean a palette?",
            answer="Artists clean a palette so the colors do not get muddy and mixed up the next time they paint.",
        ),
        QAItem(
            question="What is an art room?",
            answer="An art room is a place where people make pictures, paint, and use art tools safely.",
        ),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    lines.append(asp.fact("setting", "art_room"))
    lines.append(asp.fact("affords", "art_room", "painting"))
    lines.append(asp.fact("affords", "art_room", "mixing"))
    lines.append(asp.fact("affords", "art_room", "cleaning"))
    for pid in PALETTES:
        lines.append(asp.fact("palette", pid))
    for pid in PAINTS:
        lines.append(asp.fact("paint", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(art_room, palette_problem, happy_fix).
problem(palette_problem) :- setting(art_room), palette(wooden_palette).
fixed(happy_fix) :- problem(palette_problem), tool(rag), tool(water_cup).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("art_room", "palette_problem", "happy_fix")}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} story shape).")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="art_room", palette="wooden_palette", child_name="Mina", gender="girl", trait="curious"),
    StoryParams(place="art_room", palette="white_palette", child_name="Finn", gender="boy", trait="playful"),
]


def resolve_reasonable(args: argparse.Namespace) -> None:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.palette and args.palette not in PALETTES:
        raise StoryError("Unknown palette.")
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Unknown gender.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    resolve_reasonable(args)
    return StoryParams(
        place=args.place or "art_room",
        palette=args.palette or rng.choice(list(PALETTES)),
        child_name=args.name or rng.choice(GIRL_NAMES if (args.gender or rng.choice(["girl", "boy"])) == "girl" else BOY_NAMES),
        gender=args.gender or rng.choice(["girl", "boy"]),
        trait=args.trait or rng.choice(TRAITS),
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


def build_full_parser() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story shape:")
        for row in asp_valid():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
