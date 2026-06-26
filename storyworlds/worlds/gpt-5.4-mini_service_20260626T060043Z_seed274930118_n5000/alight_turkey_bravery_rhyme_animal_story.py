#!/usr/bin/env python3
"""
A small animal-story world about a turkey, a spark of bravery, and a rhyme that
helps the day turn alight.

Premise:
- A timid turkey wants to join a little forest rhyme circle.
- Something new and bright goes alight nearby, making the scene feel risky.
- The turkey must choose between hiding and being brave.

Turn:
- A friend or elder animal offers a simple rhyme that helps the turkey steady
  its breath and act with courage.

Resolution:
- The turkey steps forward, the rhyme gives shape to bravery, and the world
  ends with a bright image proving the turkey changed.

This file is a standalone storyworld script under the Storyweavers contract.
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
    wearing: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"turkey", "bird", "hen", "rooster"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def subject_name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the grove"
    kind: str = "outdoors"
    affords: set[str] = field(default_factory=set)


@dataclass
class Spark:
    id: str
    label: str
    verb: str
    gerund: str
    fear: str
    brave_step: str
    image: str
    keyword: str = "alight"
    tags: set[str] = field(default_factory=set)


@dataclass
class Token:
    id: str
    label: str
    phrase: str
    helps: str
    keeps: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

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
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "grove": Setting(place="the grove", kind="outdoors", affords={"rhyme", "alight"}),
    "meadow": Setting(place="the meadow", kind="outdoors", affords={"rhyme", "alight"}),
    "barnyard": Setting(place="the barnyard", kind="outdoors", affords={"rhyme"}),
}

SPARKS = {
    "lantern": Spark(
        id="lantern",
        label="a lantern",
        verb="go alight",
        gerund="glowing alight",
        fear="the bright flame might startle the birds",
        brave_step="take one careful step closer",
        image="the lantern shining gold in the dusk",
        keyword="alight",
        tags={"light", "alight", "bravery"},
    ),
    "bonfire": Spark(
        id="bonfire",
        label="a little bonfire",
        verb="burn alight",
        gerund="flickering alight",
        fear="the hot sparks might scare the turkey",
        brave_step="stand still and watch without fleeing",
        image="the bonfire tossing orange light into the dark",
        keyword="alight",
        tags={"fire", "alight", "bravery"},
    ),
}

TOKENS = {
    "rhyme": Token(
        id="rhyme",
        label="a rhyme",
        phrase="a tiny courage rhyme",
        helps="steady a worried heart",
        keeps="shape bravery into words",
        tags={"rhyme", "bravery"},
    ),
    "chorus": Token(
        id="chorus",
        label="a chorus",
        phrase="a soft chorus about feathers and dawn",
        helps="give everyone a beat to follow",
        keeps="bravery from wobbling",
        tags={"rhyme", "bravery"},
    ),
}

ANIMALS = {
    "turkey": {"type": "turkey", "label": "Turkey", "traits": ["small", "wary"]},
    "sparrow": {"type": "bird", "label": "Sparrow", "traits": ["kind", "bright"]},
    "goat": {"type": "goat", "label": "Goat", "traits": ["steady", "gentle"]},
    "hen": {"type": "hen", "label": "Hen", "traits": ["patient", "wise"]},
}

CURATED = [
    ("grove", "lantern", "rhyme"),
    ("meadow", "bonfire", "chorus"),
]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    spark: str
    token: str
    hero: str = "turkey"
    helper: str = "sparrow"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    spark = SPARKS[params.spark]
    token = TOKENS[params.token]
    hero_cfg = ANIMALS[params.hero]
    helper_cfg = ANIMALS[params.helper]

    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_cfg["type"],
        label=hero_cfg["label"],
        traits=list(hero_cfg["traits"]),
        meters={"fear": 0.0, "courage": 0.0, "joy": 0.0},
        memes={"bravery": 0.0, "rhythm": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg["type"],
        label=helper_cfg["label"],
        traits=list(helper_cfg["traits"]),
        meters={"calm": 0.0},
        memes={"kindness": 0.0},
    ))
    world.add(Entity(
        id="spark",
        kind="thing",
        type=spark.id,
        label=spark.label,
        phrase=spark.image,
    ))
    world.add(Entity(
        id="token",
        kind="thing",
        type=token.id,
        label=token.label,
        phrase=token.phrase,
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        spark=spark,
        token=token,
        setting=setting,
        hero_name=hero_cfg["label"],
        helper_name=helper_cfg["label"],
    )

    # Act 1: setup
    world.say(f"{hero.label} lived near {setting.place} and loved listening for songs in the leaves.")
    world.say(f"{hero.pronoun().capitalize()} wanted to join a little rhyme circle, but {hero.pronoun('possessive')} feet stayed shy.")
    world.say(f"Then {spark.label} went {spark.verb}, and {spark.image} made the dusk feel bright and new.")

    # Act 2: tension
    world.para()
    hero.meters["fear"] += 1.0
    world.say(f"{spark.fear}.")
    world.say(f"{hero.label} took a step back and let out a small squeak.")
    helper.memes["kindness"] += 1.0
    world.say(f"But {helper.label} came beside {hero.label} and offered {token.label}.")
    world.say(f'"{token.helps}," {helper.label} said. "{token.keeps}."')

    # Act 3: resolution
    world.para()
    hero.memes["bravery"] += 1.0
    hero.meters["courage"] += 1.0
    hero.meters["fear"] = 0.0
    world.say(f"{hero.label} breathed in time with the words and felt {token.label} settle like a tiny drumbeat.")
    world.say(f"That helped {hero.label} {spark.brave_step}, and soon {hero.pronoun()} was not hiding anymore.")
    world.say(f"{hero.label} lifted {hero.pronoun('possessive')} head, joined the rhyme, and watched {spark.label} glow peacefully in the dark.")
    world.say(f"By the end, {hero.label} was brave enough to sing, and the whole grove felt warm with rhythm and light.")

    return world


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(grove). place(meadow). place(barnyard).
affords(grove,rhyme). affords(grove,alight).
affords(meadow,rhyme). affords(meadow,alight).
affords(barnyard,rhyme).

spark(lantern). spark(bonfire).
token(rhyme). token(chorus).

valid(Place,Spark,Token) :- affords(Place,rhyme), affords(Place,alight), spark(Spark), token(Token).

#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid in SPARKS:
        lines.append(asp.fact("spark", sid))
    for tid in TOKENS:
        lines.append(asp.fact("token", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        if "rhyme" not in setting.affords or "alight" not in setting.affords:
            continue
        for spark in SPARKS:
            for token in TOKENS:
                out.append((place, spark, token))
    return out


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a young child that includes the word "{f["spark"].keyword}" and the word "turkey".',
        f"Tell a gentle story about {f['hero_name']} the turkey learning bravery with {f['helper_name']} and a rhyme.",
        f"Write a story where something goes {f['spark'].keyword} and a timid turkey becomes brave enough to sing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    spark = f["spark"]
    token = f["token"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who is the main animal in the story?",
            answer=f"The main animal is {hero.label}, a turkey who starts out shy but becomes brave.",
        ),
        QAItem(
            question=f"What went {spark.keyword} in the story?",
            answer=f"{spark.label} went {spark.keyword}, and its bright light made the grove feel alive.",
        ),
        QAItem(
            question=f"Who helped {hero.label} feel braver?",
            answer=f"{helper.label} helped by offering {token.label} and a calm rhyme to follow.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened at {place}.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"{hero.label} changed from shy to brave, and the rhyme circle became part of the bright ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something even when you feel a little scared.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern of words that sound alike at the end, which can make a song or poem fun to say.",
        ),
        QAItem(
            question="What does it mean when a lantern goes alight?",
            answer="It means the lantern starts glowing with light, like a small flame or shining lamp.",
        ),
        QAItem(
            question="What is a turkey?",
            answer="A turkey is a large bird with a fan-shaped tail and a funny walk.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: turkey, bravery, rhyme, and alight.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--spark", choices=sorted(SPARKS))
    ap.add_argument("--token", choices=sorted(TOKENS))
    ap.add_argument("--hero", choices=sorted(ANIMALS), default="turkey")
    ap.add_argument("--helper", choices=sorted(ANIMALS), default="sparrow")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.spark:
        combos = [c for c in combos if c[1] == args.spark]
    if args.token:
        combos = [c for c in combos if c[2] == args.token]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, spark, token = rng.choice(sorted(combos))
    return StoryParams(place=place, spark=spark, token=token, hero=args.hero, helper=args.helper, seed=args.seed)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, spark, token in combos:
            print(f"  {place:8} {spark:8} {token:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, spark=s, token=t)) for p, s, t in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
