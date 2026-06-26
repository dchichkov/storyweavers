#!/usr/bin/env python3
"""
A standalone story world for a tiny rhyming tale about a walrus, paints,
and a pebble, with reconciliation through dialogue and rhyme.

The domain is intentionally small and constraint-checked:
- a walrus wants to paint a pebble
- a concern arises when the paints are messy or borrowed
- the tension is resolved by conversation and a gentle compromise
- the ending proves the pebble was painted and the friendship repaired
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
    borrowed_from: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"walrus"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    light: str
    wind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    colors: set[str]
    shareable: bool = True


@dataclass
class PromptConfig:
    place: str = "the shore"
    palette: str = "bright"
    pebble_color: str = "gray"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "shore": Setting(place="the shore", light="golden", wind="soft", affords={"paint"}),
    "cove": Setting(place="the cove", light="silver", wind="brisk", affords={"paint"}),
    "dock": Setting(place="the dock", light="blue", wind="gentle", affords={"paint"}),
}

PALETTES = {
    "bright": {"red", "yellow", "blue"},
    "soft": {"pink", "mint", "lavender"},
    "sunset": {"orange", "rose", "gold"},
}

TOOL_SETS = {
    "bright": [
        Tool(id="paints", label="paints", colors={"red", "yellow", "blue"}),
    ],
    "soft": [
        Tool(id="paints", label="paints", colors={"pink", "mint", "lavender"}),
    ],
    "sunset": [
        Tool(id="paints", label="paints", colors={"orange", "rose", "gold"}),
    ],
}

PEBBLE_COLORS = ["gray", "white", "black", "golden"]


@dataclass
class StoryParams:
    place: str
    palette: str
    pebble_color: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(shore;cove;dock).
palette(bright;soft;sunset).
pebble_color(gray;white;black;golden).

valid(P, Pal, Peb) :- place(P), palette(Pal), pebble_color(Peb).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for pal in PALETTES:
        lines.append(asp.fact("palette", pal))
    for c in PEBBLE_COLORS:
        lines.append(asp.fact("pebble_color", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for palette in PALETTES:
            for peb in PEBBLE_COLORS:
                combos.append((place, palette, peb))
    return combos


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def choose_tool(palette: str) -> Tool:
    return TOOL_SETS[palette][0]


def rhyme_line(a: str, b: str) -> str:
    return f"{a} / {b}"


def can_paint(pebble: Entity, tool: Tool) -> bool:
    return bool(tool.colors)


def predict_mess(world: World, tool: Tool) -> dict[str, bool]:
    sim = world.copy()
    pebble = sim.get("pebble")
    paint = sim.get("paints")
    paint.meters["use"] = paint.meters.get("use", 0) + 1
    pebble.meters["painted"] = 1
    pebble.meters["messy"] = 1 if len(tool.colors) > 2 else 0
    return {
        "messy": pebble.meters["messy"] >= 1,
        "painted": pebble.meters["painted"] >= 1,
    }


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    world.facts.update(params=params)

    walrus = world.add(Entity(id="walrus", kind="character", type="walrus", label="the walrus"))
    pebble = world.add(Entity(id="pebble", kind="thing", type="pebble", label="the pebble", phrase=f"a {params.pebble_color} pebble"))
    paints = world.add(Entity(id="paints", kind="thing", type="paints", label="paints", phrase=f"{params.palette} paints"))

    tool = choose_tool(params.palette)
    world.facts["tool"] = tool
    world.facts["walrus"] = walrus
    world.facts["pebble"] = pebble
    world.facts["paints"] = paints

    # Beginning
    world.say(
        f"At {setting.place}, a walrus found {pebble.phrase} and {paints.label} by the water."
    )
    world.say(
        f"{walrus.pronoun('subject').capitalize()} loved to paint, and the day felt {setting.light} and {setting.wind}."
    )

    # Middle turn
    world.say(
        f"{walrus.pronoun('subject').capitalize()} wanted to paint the pebble at once, "
        f'and hummed, "A pebble can sparkle, a pebble can glow."'
    )
    world.say(
        f"But a crab from the rocks said, \"Those {paints.label} are mine to share, but please be gentle and fair.\""
    )

    prediction = predict_mess(world, tool)
    world.facts["prediction"] = prediction

    if prediction["messy"]:
        world.say(
            f"The crab worried the colors might splash and leave the pebble too messy to bear."
        )
    else:
        world.say(
            f"The crab smiled, because the colors looked tidy and kind in the air."
        )

    # Reconciliation through dialogue and rhyme
    world.say(
        f'The walrus paused and said, "I hear your care. I will paint with a light little touch."'
    )
    world.say(
        f'The crab replied, "Then we can try. A gentle reply means that this will not be too much."'
    )

    walrus.memes["concern"] = walrus.memes.get("concern", 0) + 1
    walrus.memes["reconciliation"] = walrus.memes.get("reconciliation", 0) + 1
    pebble.meters["painted"] = 1
    pebble.meters["messy"] = 0
    paints.meters["use"] = paints.meters.get("use", 0) + 1

    world.say(
        f"So the walrus painted one bright swirl, then another, with care and with glee."
    )
    world.say(
        f"The crab watched close by, and the two of them rhymed, \"Kind words make a small team free.\""
    )

    # Ending
    world.say(
        f"At last the pebble shone like a little sea jewel, and no one was cross anymore."
    )
    world.say(
        f"The walrus and the crab sat side by side, happy to share the shore."
    )

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f'Write a short rhyming story about a walrus, {p.palette} paints, and a pebble at {SETTINGS[p.place].place}.',
        "Tell a gentle dialogue-driven story where a walrus wants to paint a pebble, but someone worries first.",
        "Write a tiny reconciliation story with rhyme, painted colors, and a happy ending by the sea.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    pebble: Entity = world.facts["pebble"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who wanted to paint the pebble?",
            answer="The walrus wanted to paint the pebble.",
        ),
        QAItem(
            question="What colors were the paints?",
            answer=f"The paints were {p.palette} colors.",
        ),
        QAItem(
            question="What happened after the talk?",
            answer="The walrus and the crab talked kindly, then painted the pebble gently and made up.",
        ),
        QAItem(
            question="Was the pebble left messy?",
            answer="No. The pebble ended the story painted neatly and not messy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a walrus?",
            answer="A walrus is a large sea mammal with flippers and long tusks.",
        ),
        QAItem(
            question="What are paints for?",
            answer="Paints are used to add color to things like paper, rocks, and toys.",
        ),
        QAItem(
            question="What is a pebble?",
            answer="A pebble is a small smooth stone.",
        ),
        QAItem(
            question="Why do people use gentle words when they disagree?",
            answer="Gentle words help people understand each other and solve problems without fighting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story about a walrus, paints, and a pebble.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--palette", choices=PALETTES)
    ap.add_argument("--pebble-color", choices=PEBBLE_COLORS)
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
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.palette is None or c[1] == args.palette)
              and (args.pebble_color is None or c[2] == args.pebble_color)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, palette, pebble_color = rng.choice(sorted(combos))
    return StoryParams(place=place, palette=palette, pebble_color=pebble_color)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for palette in PALETTES:
                for peb in PEBBLE_COLORS:
                    params = StoryParams(place=place, palette=palette, pebble_color=peb, seed=base_seed)
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
