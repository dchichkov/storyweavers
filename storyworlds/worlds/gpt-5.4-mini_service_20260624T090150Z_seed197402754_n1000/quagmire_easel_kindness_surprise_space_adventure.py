#!/usr/bin/env python3
"""
A small Space Adventure storyworld about a pilot, a quagmire, an easel,
Kindness, and Surprise.

The story logic is built from a short source-tale premise:
a child on a ship wants to paint a star map, but the deck is stuck in a
quagmire; a kind helper turns the mess into a surprise rescue by using an
easel as a bridge or stand for the map.
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

THEMES = ("Kindness", "Surprise")


@dataclass
class StoryParams:
    ship: str = "the little starship"
    hero: str = "Milo"
    helper: str = "Ari"
    theme: str = "Kindness"
    twist: str = "Surprise"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        if self.kind == "character":
            return "they"
        return "it"


@dataclass
class World:
    hero: Entity
    helper: Entity
    ship: Entity
    quagmire: Entity
    easel: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SHIP_REGISTRY = {
    "starship": "a little starship",
    "rocket": "a shiny rocket",
    "freighter": "a tiny freighter",
}

HERO_NAMES = ["Milo", "Nia", "Tess", "Rio", "Luna", "Jax"]
HELPER_NAMES = ["Ari", "Zee", "Pia", "Orin", "Sage", "Bea"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with quagmire and easel.")
    ap.add_argument("--ship", choices=SHIP_REGISTRY)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--theme", choices=list(THEMES))
    ap.add_argument("--twist", choices=list(THEMES))
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
    theme = args.theme or rng.choice(THEMES)
    twist = args.twist or ("Surprise" if theme == "Kindness" else "Kindness")
    ship = args.ship or rng.choice(list(SHIP_REGISTRY))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    return StoryParams(ship=ship, hero=hero, helper=helper, theme=theme, twist=twist)


def build_world(params: StoryParams) -> World:
    hero = Entity("hero", "character", params.hero, "pilot")
    helper = Entity("helper", "character", params.helper, "friend")
    ship = Entity("ship", "thing", SHIP_REGISTRY[params.ship], params.ship)
    quagmire = Entity("quagmire", "thing", "the sticky quagmire", "quagmire")
    easel = Entity("easel", "thing", "an old easel", "easel")
    return World(hero=hero, helper=helper, ship=ship, quagmire=quagmire, easel=easel)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, label in SHIP_REGISTRY.items():
        lines.append(asp.fact("ship_kind", sid))
        lines.append(asp.fact("ship_label", sid, label))
    lines.append(asp.fact("scene", "space_dock"))
    lines.append(asp.fact("hazard", "quagmire"))
    lines.append(asp.fact("tool", "easel"))
    lines.append(asp.fact("theme", "kindness"))
    lines.append(asp.fact("theme", "surprise"))
    return "\n".join(lines)


ASP_RULES = r"""
allowed_story(S, H, T) :- ship_kind(S), hero_name(H), theme_word(T).
#show allowed_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show allowed_story/3."))
    atoms = set(asp.atoms(model, "allowed_story"))
    expected = {(sid, h, t) for sid in SHIP_REGISTRY for h in HERO_NAMES for t in ("kindness", "surprise")}
    if atoms == expected:
        print(f"OK: ASP gate matches Python registry ({len(atoms)} combos).")
        return 0
    print("MISMATCH between ASP and Python registries.")
    return 1


def generate_story(world: World, params: StoryParams) -> None:
    hero, helper, ship, quagmire, easel = world.hero, world.helper, world.ship, world.quagmire, world.easel

    world.say(
        f"{hero.label} loved flying {ship.label} through the calm blue lanes between moons."
    )
    world.say(
        f"One day, {hero.label} found a map table near the dock, and {easel.label} stood there like a tall little ladder."
    )

    world.para()
    quagmire.meters["stickiness"] = 1
    hero.memes["surprise"] = 1
    world.say(
        f"But the landing pad had sunk into a strange quagmire of glittery mud, and that was a surprise."
    )
    world.say(
        f"{hero.label} wanted to paint a star map for the crew, but the wobbling ground made every step slow."
    )

    world.para()
    helper.memes["kindness"] = 1
    world.say(
        f"{helper.label} saw the problem and smiled with kindness."
    )
    world.say(
        f"Together they dragged {easel.label} beside the quagmire and laid a board across it like a tiny bridge."
    )

    world.para()
    hero.memes["joy"] = 1
    world.say(
        f"Then came the best surprise of all: the easel held the map steady, and the paint stayed neat."
    )
    world.say(
        f"{hero.label} painted bright planets while {helper.label} held the page, and the ship gleamed in the sunset."
    )
    world.say(
        f"In the end, kindness turned the quagmire into a safe path, and surprise made the whole dock feel magical."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        ship=ship,
        quagmire=quagmire,
        easel=easel,
        theme=params.theme,
        twist=params.twist,
    )


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"].label
    helper = world.facts["helper"].label
    ship = world.facts["ship"].label
    return [
        QAItem(
            question=f"Who wanted to paint a star map on {ship}?",
            answer=f"{hero} wanted to paint a star map on {ship}.",
        ),
        QAItem(
            question="What problem blocked the landing pad?",
            answer="A strange quagmire of glittery mud blocked the landing pad.",
        ),
        QAItem(
            question=f"Who helped with kindness?",
            answer=f"{helper} helped with kindness.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an easel for?",
            answer="An easel is a stand that helps hold up a picture or a page while someone paints or draws.",
        ),
        QAItem(
            question="What is a quagmire?",
            answer="A quagmire is a soft, sticky muddy place that can trap feet and make walking hard.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, helpful, and caring to someone else.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes people widen their eyes or smile.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Space Adventure story for a child that includes "{f["ship"].label}", quagmire, and easel.',
        f"Tell a gentle story where {f['hero'].label} and {f['helper'].label} solve a muddy space problem with kindness.",
        f"Write a simple adventure with a surprise ending about a ship, a quagmire, and an easel.",
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
    lines = ["--- world model state ---"]
    for e in [world.hero, world.helper, world.ship, world.quagmire, world.easel]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {e.label} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(ship="starship", hero="Milo", helper="Ari", theme="Kindness", twist="Surprise"),
    StoryParams(ship="rocket", hero="Nia", helper="Bea", theme="Surprise", twist="Kindness"),
    StoryParams(ship="freighter", hero="Luna", helper="Sage", theme="Kindness", twist="Surprise"),
]


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
        print(asp_program("#show allowed_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show allowed_story/3."))
        print(sorted(asp.atoms(model, "allowed_story")))
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
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
