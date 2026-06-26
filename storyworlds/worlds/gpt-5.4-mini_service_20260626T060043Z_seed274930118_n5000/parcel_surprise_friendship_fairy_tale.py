#!/usr/bin/env python3
"""
storyworlds/worlds/parcel_surprise_friendship_fairy_tale.py
============================================================

A small fairy-tale story world about a parcel, a surprise, and a friendship
that grows because of it.

Premise:
- A child or small creature in a fairy-tale setting receives a parcel.
- The parcel contains a surprising gift or message.
- The surprise begins with caution or puzzlement, then turns into friendship.
- The ending proves the change in the world state.

The story engine keeps a simple simulated model with physical meters and
emotional memes, so the narration follows what actually changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carries: Optional[str] = None
    holds: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "witch"}
        male = {"boy", "king", "prince", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"heavy": 0.0, "sealed": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "fear": 0.0, "surprise": 0.0, "friendship": 0.0, "trust": 0.0}


@dataclass
class Setting:
    place: str
    indoors: bool = False
    mood: str = "gentle"


@dataclass
class Parcel:
    label: str
    phrase: str
    surprise: str
    opener: str
    gift: str
    friendship_boost: float
    reveal_word: str = "surprise"


@dataclass
class StoryParams:
    setting: str
    parcel: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_sealed_breaks(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "thing":
            continue
        if e.meters.get("sealed", 0) >= THRESHOLD and e.holds:
            sig = ("sealed", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"{e.label.capitalize()} stayed sealed and waited for careful hands.")
    return out


CAUSAL_RULES = [
    Rule("sealed_breaks", _r_sealed_breaks),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "forest": Setting(place="the moonlit forest", indoors=False, mood="gentle"),
    "cottage": Setting(place="the little cottage", indoors=True, mood="warm"),
    "garden": Setting(place="the rose garden", indoors=False, mood="bright"),
}

PARCELS = {
    "bells": Parcel(
        label="parcel of silver bells",
        phrase="a small parcel tied with blue ribbon",
        surprise="a tiny bell that rang like laughter",
        opener="untied the ribbon",
        gift="silver bells",
        friendship_boost=2.0,
    ),
    "bread": Parcel(
        label="parcel of sweet bread",
        phrase="a warm parcel wrapped in linen",
        surprise="a loaf of honey bread and a note",
        opener="opened the cloth",
        gift="honey bread",
        friendship_boost=1.5,
    ),
    "seed": Parcel(
        label="parcel of glowing seeds",
        phrase="a little parcel with a wax seal",
        surprise="glowing seeds that could bloom at night",
        opener="broke the seal",
        gift="glowing seeds",
        friendship_boost=2.5,
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tilda", "Nora", "Elin", "Rosa"]
BOY_NAMES = ["Pip", "Tobin", "Jasper", "Eli", "Rowan", "Finn"]
HELPER_NAMES = ["Moth", "Bram", "Hazel", "Willow", "Robin", "Puck"]
TRAITS = ["brave", "curious", "gentle", "lonely", "cheerful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, p) for s in SETTINGS for p in PARCELS]


def explain_invalid(parcel_id: str) -> str:
    return f"(No story: the parcel {parcel_id!r} is unknown in this fairy-tale world.)"


def tell(setting: Setting, parcel_def: Parcel, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        traits=["small", "kind"],
    ))
    parcel = world.add(Entity(
        id="parcel",
        kind="thing",
        type="parcel",
        label=parcel_def.label,
        phrase=parcel_def.phrase,
        owner=helper.id,
        holds=hero.id,
    ))
    parcel.meters["sealed"] = 1.0
    hero.memes["curiosity"] += 1.0
    hero.memes["fear"] += 0.5

    world.say(
        f"In {setting.place}, there lived a little {trait} {hero_type} named {hero_name}."
    )
    world.say(
        f"One misty evening, {hero_name} found {parcel.phrase} waiting by the gate."
    )
    world.say(
        f"{hero_name} wondered who had sent it, because the ribbon was neat and the parcel was too quiet."
    )

    world.para()
    world.say(
        f"Then {helper_name} appeared from the path, smiling softly."
    )
    world.say(
        f'"I brought you this parcel," {helper_name} said. "Please {parcel_def.opener}."'
    )
    hero.memes["curiosity"] += 1.0
    parcel.meters["sealed"] = 0.0

    world.para()
    world.say(
        f"{hero_name} took a breath and {parcel_def.opener}."
    )
    hero.memes["surprise"] += 1.0
    world.say(
        f"Inside was {parcel_def.surprise}."
    )
    world.say(
        f"{hero_name} laughed at the lovely surprise, and {helper_name} laughed too."
    )
    helper.memes["trust"] += 1.0
    helper.memes["friendship"] += 1.0
    hero.memes["friendship"] += parcel_def.friendship_boost
    hero.memes["trust"] += 1.0

    world.para()
    world.say(
        f"They shared {parcel_def.gift}, and the night felt warmer for both of them."
    )
    world.say(
        f"Before long, {hero_name} and {helper_name} were friends, walking home under the stars."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        parcel=parcel,
        parcel_def=parcel_def,
        setting=setting,
        surprise=parcel_def.surprise,
    )
    propagate(world, narrate=False)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for young children about a {f["parcel_def"].label} in {f["setting"].place}.',
        f'Tell a gentle story where {f["hero"].id} opens a parcel and discovers a surprise that leads to friendship.',
        f'Write a short magical story with a parcel, a surprise inside, and two characters becoming friends.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parcel_def = f["parcel_def"]
    return [
        QAItem(
            question=f"Who found the parcel in the story?",
            answer=f"{hero.id} found the parcel in {world.setting.place}.",
        ),
        QAItem(
            question=f"What was inside the parcel?",
            answer=f"Inside was {parcel_def.surprise}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the parcel was opened?",
            answer=f"{hero.id} felt surprised, then happy, because the parcel held a kind gift.",
        ),
        QAItem(
            question=f"What happened between {hero.id} and {helper.id} by the end?",
            answer=f"They became friends and shared the gift together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parcel?",
            answer="A parcel is a package sent or carried to someone, often tied up or wrapped to keep the contents safe.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that can make someone gasp, smile, or laugh with delight.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a warm bond between people who care for each other, help each other, and enjoy being together.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} ({e.kind:8}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    setting: str
    parcel: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale parcel storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--parcel", choices=PARCELS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "child"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy", "child"])
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.parcel:
        combos = [c for c in combos if c[1] == args.parcel]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, parcel = rng.choice(combos)
    parcel_def = PARCELS[parcel]
    hero_type = args.hero_type or rng.choice(["girl", "boy", "child"])
    if hero_type == "girl":
        hero_name = args.name or rng.choice(GIRL_NAMES)
    elif hero_type == "boy":
        hero_name = args.name or rng.choice(BOY_NAMES)
    else:
        hero_name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["girl", "boy", "child"])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, parcel, hero_name, hero_type, helper_name, helper_type, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PARCELS[params.parcel],
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
        params.trait,
    )
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


ASP_RULES = r"""
setting(S) :- location(S).
parcel(P) :- package(P).

compatible(S,P) :- setting(S), parcel(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("location", s))
    for p in PARCELS:
        lines.append(asp.fact("package", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting, parcel in valid_combos():
            params = StoryParams(
                setting=setting,
                parcel=parcel,
                hero_name="Lina",
                hero_type="girl",
                helper_name="Moth",
                helper_type="child",
                trait="curious",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
