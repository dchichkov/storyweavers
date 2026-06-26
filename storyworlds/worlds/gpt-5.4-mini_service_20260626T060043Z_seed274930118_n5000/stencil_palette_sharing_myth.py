#!/usr/bin/env python3
"""
storyworlds/worlds/stencil_palette_sharing_myth.py
===================================================

A small mythic storyworld about sharing a stencil and a palette.

Premise:
- A child artist receives a stencil and a palette.
- A sibling, friend, or helper needs one of the tools to finish a mural.
- The first child must decide whether to keep, lend, or share.
- A gentle turn shows that sharing makes the picture better and the bond stronger.

The world is intentionally tiny and constraint-checked:
- The stencil has a shape, and the palette has colors.
- Only some shapes want some colors.
- A shared tool can be passed, returned, or used together.
- The story ends with a visible change in the mural and in the characters' feelings.

This script follows the Storyweavers contract and includes:
- StoryParams
- registries
- build_parser, resolve_params, generate, emit, main
- QAItem / StoryError / StorySample
- inline ASP_RULES twin and asp_facts()
- --verify parity checks and sample story exercise
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    shared_with: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the workshop"
    mood: str = "quiet"
    affords: set[str] = field(default_factory=set)


@dataclass
class Stencil:
    label: str
    phrase: str
    shape: str
    theme: str
    fits_colors: set[str]
    shared_use: bool = True


@dataclass
class Palette:
    label: str
    phrase: str
    colors: list[str]
    bright: bool = True
    shared_use: bool = True


@dataclass
class StoryParams:
    place: str
    stencil: str
    palette: str
    hero: str
    hero_type: str
    other: str
    other_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
    "studio": Setting(place="the little studio", mood="still", affords={"paint"}),
    "courtyard": Setting(place="the sunlit courtyard", mood="open", affords={"paint"}),
    "hall": Setting(place="the long hall", mood="echoing", affords={"paint"}),
}

STENCILS = {
    "star": Stencil(
        label="a star stencil",
        phrase="a star-shaped stencil with smooth edges",
        shape="star",
        theme="night",
        fits_colors={"gold", "blue", "white"},
    ),
    "fish": Stencil(
        label="a fish stencil",
        phrase="a fish stencil with a curling tail",
        shape="fish",
        theme="river",
        fits_colors={"blue", "green", "silver"},
    ),
    "tree": Stencil(
        label="a tree stencil",
        phrase="a tree stencil with many leaf holes",
        shape="tree",
        theme="forest",
        fits_colors={"green", "brown", "gold"},
    ),
    "bird": Stencil(
        label="a bird stencil",
        phrase="a bird stencil with wide wing cutouts",
        shape="bird",
        theme="sky",
        fits_colors={"white", "gold", "blue"},
    ),
}

PALETTES = {
    "dawn": Palette(
        label="a dawn palette",
        phrase="a palette full of pale dawn colors",
        colors=["white", "gold", "pink"],
    ),
    "river": Palette(
        label="a river palette",
        phrase="a palette full of river colors",
        colors=["blue", "green", "silver"],
    ),
    "forest": Palette(
        label="a forest palette",
        phrase="a palette full of forest colors",
        colors=["green", "brown", "gold"],
    ),
    "sun": Palette(
        label="a sun palette",
        phrase="a palette glowing with bright sun colors",
        colors=["gold", "orange", "white"],
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Sera", "Nia", "Tala", "Iris", "Luna", "Zora"]
BOY_NAMES = ["Ari", "Niko", "Theo", "Milo", "Jaro", "Dane", "Cai", "Eli"]
TRAITS = ["careful", "bold", "gentle", "curious", "patient", "bright"]


def compatible(stencil: Stencil, palette: Palette) -> bool:
    return bool(set(palette.colors) & stencil.fits_colors)


def explain_rejection(stencil: Stencil, palette: Palette) -> str:
    return (
        f"(No story: {stencil.label} and {palette.label} do not match well enough "
        f"for a shared mural. The palette colors do not fit the stencil's theme.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for s_id, s in STENCILS.items():
            for p_id, p in PALETTES.items():
                if place in SETTINGS and compatible(s, p):
                    out.append((place, s_id, p_id))
    return out


def valid_story_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, s_id, p_id in valid_combos():
        for gender in ("girl", "boy"):
            out.append((place, s_id, p_id, gender))
    return out


def art_delight(stencil: Stencil, palette: Palette) -> str:
    return {
        "star": "the stars looked like little fires in the dark",
        "fish": "the fish looked as if it could swim off the wall",
        "tree": "the leaves seemed to rustle even while they were still",
        "bird": "the bird seemed ready to lift into the air",
    }.get(stencil.shape, "the mural seemed to wake up")


def shared_turn(stencil: Stencil, palette: Palette) -> str:
    return {
        "star": "they painted the points together, one holding the stencil and one brushing gold into the gaps",
        "fish": "they passed the palette back and forth, one tracing the curve while the other filled it with blue",
        "tree": "they worked leaf by leaf, sharing the brush and the colors until the branches glowed",
        "bird": "they shared the palette in silence, one shaping the wings while the other touched them with bright light",
    }.get(stencil.shape, "they worked together until the picture changed")


def setting_detail(setting: Setting) -> str:
    return {
        "the little studio": "The little studio smelled like paper, water, and warm dust.",
        "the sunlit courtyard": "Sunlight lay on the stones like a soft blanket.",
        "the long hall": "The long hall echoed each step as if it were waiting for a song.",
    }.get(setting.place, f"{setting.place.capitalize()} waited quietly for the first stroke.")


def introduction(world: World, hero: Entity, other: Entity, stencil: Stencil, palette: Palette) -> None:
    world.say(
        f"{hero.id} was a {hero.pronoun('possessive')} {hero.memes.get('trait', 'careful')} {hero.type} who loved making pictures."
    )
    world.say(
        f"One day, {hero.id} found {stencil.label} and {palette.label}, and {hero.pronoun()} felt proud of the shining tools."
    )
    world.say(
        f"{other.id} was a {other.pronoun('possessive')} {other.memes.get('trait', 'gentle')} {other.type} who wanted to help with the mural too."
    )


def tension(world: World, hero: Entity, other: Entity, stencil: Stencil, palette: Palette) -> None:
    hero.memes["guarding"] = hero.memes.get("guarding", 0) + 1
    other.memes["hope"] = other.memes.get("hope", 0) + 1
    world.para()
    world.say(setting_detail(world.setting))
    world.say(
        f"{other.id} asked to share the {stencil.label.split()[-2]} and the colors, but {hero.id} hugged the tools close at first."
    )
    world.say(
        f"{hero.id} feared the mural would be spoiled, while {other.id} feared being left out."
    )
    if compatible(stencil, palette):
        world.say(
            f"Yet the tools had been made for one another: {stencil.shape} and the {palette.label.split()[1]} colors promised a true picture."
        )


def resolve(world: World, hero: Entity, other: Entity, stencil: Stencil, palette: Palette) -> None:
    hero.memes["guarding"] = max(0.0, hero.memes.get("guarding", 0) - 1)
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    other.memes["joy"] = other.memes.get("joy", 0) + 1
    hero.memes["bond"] = hero.memes.get("bond", 0) + 1
    other.memes["bond"] = other.memes.get("bond", 0) + 1
    world.para()
    world.say(
        f"Then {hero.id} remembered that a shared hand can make a stronger line than a lonely one."
    )
    world.say(
        f"{hero.id} gave {other.id} the stencil, and they shared the palette so each color could find its place."
    )
    world.say(shared_turn(stencil, palette) + ".")
    world.say(
        f"By the end, {art_delight(stencil, palette)}; {hero.id} and {other.id} stood side by side, smiling at the wall."
    )


def tell(setting: Setting, stencil: Stencil, palette: Palette, hero_name: str, hero_type: str,
         other_name: str, other_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"trait": trait}))
    other = world.add(Entity(id=other_name, kind="character", type=other_type, memes={"trait": "gentle"}))
    world.facts.update(hero=hero, other=other, stencil=stencil, palette=palette, setting=setting)
    world.say(
        f"In {setting.place}, {hero.id} found {stencil.label} and {palette.label} beside a blank wall."
    )
    introduction(world, hero, other, stencil, palette)
    tension(world, hero, other, stencil, palette)
    resolve(world, hero, other, stencil, palette)
    world.facts.update(resolved=True)
    return world


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in STENCILS.items():
        lines.append(asp.fact("stencil", sid))
        lines.append(asp.fact("shape", sid, s.shape))
        lines.append(asp.fact("theme", sid, s.theme))
        for c in sorted(s.fits_colors):
            lines.append(asp.fact("fits_color", sid, c))
    for pid, p in PALETTES.items():
        lines.append(asp.fact("palette", pid))
        for c in p.colors:
            lines.append(asp.fact("color", pid, c))
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for g in ("girl", "boy"):
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S,P) :- stencil(S), palette(P), fits_color(S,C), color(P,C).
valid(Place,S,P) :- place(Place), compatible(S,P).
valid_story(Place,S,P,G) :- valid(Place,S,P), gender(G).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between ASP and Python valid_combos():")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        return 1
    sample_params = resolve_params(argparse.Namespace(
        place=None, stencil=None, palette=None, gender=None, hero=None, other=None, trait=None
    ), random.Random(7))
    generate(sample_params)
    print(f"OK: ASP matches Python ({len(py)} combos); sample story generated.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld of sharing a stencil and a palette.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--stencil", choices=STENCILS)
    ap.add_argument("--palette", choices=PALETTES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--other")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.stencil is None or c[1] == args.stencil)
              and (args.palette is None or c[2] == args.palette)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, stencil_id, palette_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    other = args.other or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, stencil=stencil_id, palette=palette_id,
                       hero=hero, hero_type=gender, other=other, other_type="friend",
                       trait=trait)


def generate(params: StoryParams) -> StorySample:
    stencil = STENCILS[params.stencil]
    palette = PALETTES[params.palette]
    if not compatible(stencil, palette):
        raise StoryError(explain_rejection(stencil, palette))
    world = tell(SETTINGS[params.place], stencil, palette,
                 params.hero, params.hero_type, params.other, params.other_type, params.trait)
    prompts = [
        f"Write a myth-like story about a child who must share {stencil.label} and {palette.label}.",
        f"Tell a gentle tale where {params.hero} learns to share a stencil and a palette with another child.",
        f"Create a child-friendly myth about making one mural from two hands and shared colors.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.hero} stop holding the tools alone?",
            answer=f"{params.hero} realized the mural would be better if {params.other} could help, so the stencil and palette were shared.",
        ),
        QAItem(
            question=f"What did the shared stencil and palette help them make?",
            answer=f"They helped make a mural that matched the stencil's shape and the palette's colors.",
        ),
        QAItem(
            question=f"How did {params.hero} feel at the end?",
            answer=f"{params.hero} felt happy and proud, because sharing turned the work into a joint picture instead of a lonely one.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a stencil?",
            answer="A stencil is a flat template with cutout shapes that helps you paint the same design again and again.",
        ),
        QAItem(
            question="What is a palette?",
            answer="A palette is a board or tray that holds paint colors so an artist can mix and share them while working.",
        ),
        QAItem(
            question="Why do people share art tools?",
            answer="People share art tools so everyone can help make the picture, and the work can be finished together.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    out.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} memes={e.memes} meters={e.meters}")
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


CURATED = [
    StoryParams(place="studio", stencil="star", palette="dawn", hero="Mira", hero_type="girl", other="Ari", other_type="friend", trait="careful"),
    StoryParams(place="courtyard", stencil="fish", palette="river", hero="Theo", hero_type="boy", other="Lina", other_type="friend", trait="bold"),
    StoryParams(place="hall", stencil="tree", palette="forest", hero="Nia", hero_type="girl", other="Milo", other_type="friend", trait="gentle"),
]


def asp_show_program() -> str:
    return asp_program("#show valid_story/4.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, stencil, palette) combos ({len(stories)} with gender):\n")
        for place, s, p in triples:
            genders = sorted(g for (pl, ss, pp, g) in stories if (pl, ss, pp) == (place, s, p))
            print(f"  {place:10} {s:8} {p:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
