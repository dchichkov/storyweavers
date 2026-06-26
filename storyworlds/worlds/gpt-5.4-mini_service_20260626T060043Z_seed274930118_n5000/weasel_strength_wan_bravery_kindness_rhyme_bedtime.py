#!/usr/bin/env python3
"""
A tiny bedtime-story world about a weasel, a wan evening, and the quiet forms
of strength that come from bravery, kindness, and rhyme.

Seed inspiration:
- weasel
- strength
- wan

Premise:
A small weasel named Wren feels too wan and wobbly to settle for sleep. The
night is soft and a little scary, so Wren searches for strength in brave
breaths, kind help, and a calming rhyme. The story turns when Wren learns that
strength can be gentle, and bedtime can become bright and safe.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"weasel"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    dimness: str
    sounds: str


@dataclass
class StoryParams:
    place: str
    weasel_name: str
    moon_style: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "burrow": Place(name="the burrow", dimness="soft and warm", sounds="the hush of blankets"),
    "meadow_edge": Place(name="the meadow edge", dimness="wan and silver", sounds="the rustle of grass"),
    "moon_nook": Place(name="the moon nook", dimness="pale and calm", sounds="the sigh of night air"),
}

MOON_STYLES = {
    "wan": "wan",
    "silver": "silver",
    "round": "round",
}

NAMES = ["Wren", "Milo", "Pip", "Luna", "Bram", "Tess"]


@dataclass
class Feature:
    name: str
    meter_key: str
    gain: float
    text: str


FEATURES = {
    "bravery": Feature(
        name="Bravery",
        meter_key="bravery",
        gain=1.0,
        text="a brave breath",
    ),
    "kindness": Feature(
        name="Kindness",
        meter_key="kindness",
        gain=1.0,
        text="a kind helping paw",
    ),
    "rhyme": Feature(
        name="Rhyme",
        meter_key="rhyme",
        gain=1.0,
        text="a sleepy little rhyme",
    ),
}


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def story_intro(world: World, weasel: Entity) -> None:
    world.say(
        f"In {world.place.name}, the night was {world.place.dimness}, and {world.place.sounds} drifted through the air."
    )
    world.say(
        f"{weasel.id} was a little weasel with soft fur and a quiet heart."
    )


def feel_wan(world: World, weasel: Entity) -> None:
    weasel.meters["wan"] = 1.0
    weasel.memes["tired"] = 1.0
    world.say(
        f"But tonight {weasel.id} felt wan and small, as if the moon had washed all the color from the room."
    )


def worry_about_sleep(world: World, weasel: Entity) -> None:
    weasel.memes["worry"] = 1.0
    world.say(
        f"{weasel.id} wanted to sleep, yet the dark corners looked too big for such a tiny weasel."
    )


def brave_breath(world: World, weasel: Entity) -> None:
    feature = FEATURES["bravery"]
    weasel.memes[feature.meter_key] = weasel.memes.get(feature.meter_key, 0.0) + feature.gain
    weasel.meters["steady"] = weasel.meters.get("steady", 0.0) + 1.0
    world.say(
        f"So {weasel.id} took {feature.text} and held it close like a warm pebble in a paw."
    )


def kind_help(world: World, weasel: Entity) -> None:
    feature = FEATURES["kindness"]
    weasel.memes[feature.meter_key] = weasel.memes.get(feature.meter_key, 0.0) + feature.gain
    world.say(
        f"Then {weasel.id} saw a blanket folded crookedly and straightened it with {feature.text}."
    )


def rhyme_time(world: World, weasel: Entity) -> None:
    feature = FEATURES["rhyme"]
    weasel.memes[feature.meter_key] = weasel.memes.get(feature.meter_key, 0.0) + feature.gain
    world.say(
        f"{weasel.id} whispered a {feature.text}: 'Moon so wan, stay close to me; night is kind and safe as can be.'"
    )


def settle_for_sleep(world: World, weasel: Entity) -> None:
    weasel.meters["wan"] = 0.0
    weasel.memes["worry"] = 0.0
    weasel.memes["rest"] = 1.0
    world.say(
        f"The rhyme made the room feel smaller and safer. {weasel.id} curled up, and the wan feeling drifted away."
    )
    world.say(
        f"At last {weasel.id} slept soundly, with bravery, kindness, and rhyme tucked under the blankets like stars."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def tell(place: Place, weasel_name: str, moon_style: str) -> World:
    world = World(place)
    weasel = world.add(Entity(
        id=weasel_name,
        kind="character",
        type="weasel",
        label="weasel",
        meters={"wan": 0.0, "steady": 0.0},
        memes={"tired": 0.0, "worry": 0.0, "bravery": 0.0, "kindness": 0.0, "rhyme": 0.0, "rest": 0.0},
    ))
    moon = world.add(Entity(
        id="moon",
        kind="thing",
        type="moon",
        label=f"{moon_style} moon",
        phrase=f"a {moon_style} moon",
        meters={"bright": 1.0},
    ))

    world.facts.update(weasel=weasel, moon=moon, place=place, moon_style=moon_style)

    story_intro(world, weasel)
    feel_wan(world, weasel)
    worry_about_sleep(world, weasel)
    brave_breath(world, weasel)
    kind_help(world, weasel)
    rhyme_time(world, weasel)
    settle_for_sleep(world, weasel)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    w = f["weasel"]
    return [
        f"Write a bedtime story about a little weasel named {w.id} who feels wan and finds strength through bravery, kindness, and rhyme.",
        f"Tell a gentle night story set in {f['place'].name} where {w.id} calms down with a {f['moon_style']} moon overhead.",
        "Write a short bedtime tale where a tiny weasel learns that being brave and kind can make sleep feel safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    w = f["weasel"]
    place = f["place"].name
    moon_style = f["moon_style"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {w.id}, a little weasel who lives through a quiet bedtime worry and then settles into sleep.",
        ),
        QAItem(
            question=f"Where does the bedtime story happen?",
            answer=f"It happens in {place}, where the night is soft and the sounds are gentle.",
        ),
        QAItem(
            question=f"What made {w.id} feel better before sleep?",
            answer=f"{w.id} felt better after taking a brave breath, helping with kindness, and whispering a rhyme under the {moon_style} moon.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {w.id} was no longer wan or worried. The little weasel felt safe enough to sleep soundly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is the feeling that helps someone do something even when they feel afraid or shy.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle and helpful to someone else.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern of words that sound alike at the end, like a little song for the ears.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(burrow).
place(meadow_edge).
place(moon_nook).

moon_style(wan).
moon_style(silver).
moon_style(round).

feature(bravery).
feature(kindness).
feature(rhyme).

compatible(P, M, F) :- place(P), moon_style(M), feature(F).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MOON_STYLES:
        lines.append(asp.fact("moon_style", m))
    for f in FEATURES:
        lines.append(asp.fact("feature", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatibility() -> set[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return set(asp.atoms(model, "compatible"))


def python_compatibility() -> set[tuple[str, str, str]]:
    out = set()
    for p in PLACES:
        for m in MOON_STYLES:
            for f in FEATURES:
                out.add((p, m, f))
    return out


def asp_verify() -> int:
    a = asp_compatibility()
    b = python_compatibility()
    if a == b:
        print(f"OK: clingo gate matches python compatibility ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python compatibility:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    weasel_name: str
    moon_style: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about a weasel, wan moonlight, and quiet strength.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", dest="weasel_name", choices=NAMES)
    ap.add_argument("--moon-style", choices=MOON_STYLES)
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
    place = args.place or rng.choice(list(PLACES))
    weasel_name = args.weasel_name or rng.choice(NAMES)
    moon_style = args.moon_style or rng.choice(list(MOON_STYLES))
    return StoryParams(place=place, weasel_name=weasel_name, moon_style=moon_style)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.weasel_name, MOON_STYLES[params.moon_style])
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
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(place="burrow", weasel_name="Wren", moon_style="wan"),
    StoryParams(place="meadow_edge", weasel_name="Pip", moon_style="silver"),
    StoryParams(place="moon_nook", weasel_name="Luna", moon_style="wan"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = sorted(asp_compatibility())
        print(f"{len(combos)} compatible place/moon/feature triples:")
        for p, m, f in combos:
            print(f"  {p:12} {m:8} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.weasel_name}: {p.place} / {p.moon_style}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
