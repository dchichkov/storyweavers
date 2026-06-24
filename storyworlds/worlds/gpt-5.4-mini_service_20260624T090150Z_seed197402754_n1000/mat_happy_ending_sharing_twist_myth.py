#!/usr/bin/env python3
"""
A myth-style story world about a mat, a sharing problem, a twist, and a happy ending.

The seed tale imagines a small, classical premise:
- a child or animal-hero treasures a mat,
- someone wants to use it too,
- a twist reveals the mat has a second purpose,
- sharing leads to a warm ending image.

The world is kept small and state-driven so stories can vary while staying causal.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    partner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "sister"}
        male = {"boy", "father", "man", "king", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the meadow"
    light: str = "golden"
    kind: str = "outdoor"


@dataclass
class Mat:
    id: str
    label: str
    phrase: str
    purpose: str
    texture: str
    size: str = "small"
    plural: bool = False


@dataclass
class Twist:
    id: str
    reveal: str
    helps: str
    outcome: str


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a mat, a sharing twist, and a happy ending.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--hero", choices=["girl", "boy", "queen", "king", "sister", "brother"])
    ap.add_argument("--name")
    ap.add_argument("--place", choices=["meadow", "hut", "riverbank", "court", "garden"])
    ap.add_argument("--mat", choices=["sleep", "picnic", "prayer", "dance"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


SETTINGS = {
    "meadow": Setting("the meadow", "golden", "outdoor"),
    "hut": Setting("the hut", "dim", "indoor"),
    "riverbank": Setting("the riverbank", "silver", "outdoor"),
    "court": Setting("the court", "bright", "indoor"),
    "garden": Setting("the garden", "soft", "outdoor"),
}

MATS = {
    "sleep": Mat("sleep", "sleep mat", "a woven sleep mat", "rest", "soft"),
    "picnic": Mat("picnic", "picnic mat", "a bright picnic mat", "sharing food", "striped"),
    "prayer": Mat("prayer", "prayer mat", "a prayer mat with a blue edge", "quiet devotion", "ornate"),
    "dance": Mat("dance", "dance mat", "a round dance mat", "dancing together", "firm"),
}

TWISTS = {
    "softness": Twist("softness", "the mat was softer than it looked", "children could sit together", "they made room and shared it"),
    "pattern": Twist("pattern", "the pattern on the mat showed two birds facing each other", "it seemed made for two", "they took it as a sign to share"),
    "hidden": Twist("hidden", "there was a second folded mat hidden underneath", "no one had to wait alone", "they unfolded both and sat side by side"),
}

NAMES = {
    "girl": ["Mira", "Luna", "Sana", "Asha", "Tala"],
    "boy": ["Arun", "Kavi", "Niko", "Ravi", "Taro"],
    "queen": ["Nyra", "Isha", "Mira"],
    "king": ["Orin", "Dara", "Soren"],
    "sister": ["Mina", "Lila", "Tara"],
    "brother": ["Bela", "Ravi", "Arin"],
}

TRAITS = ["gentle", "brave", "curious", "kind", "quiet"]


def choose_combo(rng: random.Random, args: argparse.Namespace) -> tuple[str, str, str, str]:
    place = args.place or rng.choice(list(SETTINGS))
    mat = args.mat or rng.choice(list(MATS))
    hero_type = args.hero or rng.choice(["girl", "boy", "queen", "king", "sister", "brother"])
    name = args.name or rng.choice(NAMES[hero_type])
    return place, mat, hero_type, name


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    place, mat, hero_type, name = choose_combo(rng, args)
    if place not in SETTINGS or mat not in MATS:
        raise StoryError("No valid story matched the requested options.")
    return StoryParams(
        place=place,
        mat=mat,
        hero_type=hero_type,
        name=name,
        trait=args.__dict__.get("trait") or rng.choice(TRAITS),
        seed=None,
    )


@dataclass
class StoryParams:
    place: str
    mat: str
    hero_type: str
    name: str
    trait: str
    seed: Optional[int] = None


def needs_sharing(world: World, hero: Entity, mat: Entity) -> bool:
    return hero.memes.get("want_mat", 0.0) >= THRESHOLD and mat.memes.get("claim", 0.0) >= THRESHOLD


def tell(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type))
    other = world.add(Entity(id="Guest", kind="character", type="child"))
    mat = world.add(Entity(
        id="mat",
        type="mat",
        label=MATS[params.mat].label,
        phrase=MATS[params.mat].phrase,
        owner=hero.id,
        plural=MATS[params.mat].plural,
    ))
    twist = TWISTS[rng.choice(list(TWISTS))]
    world.facts.update(hero=hero, other=other, mat=mat, twist=twist, setting=world.setting, params=params)

    hero.memes["love"] = 1.0
    mat.memes["claim"] = 1.0
    world.say(f"In {world.setting.place}, there was {hero.pronoun('possessive')} {mat.phrase}.")
    world.say(f"{hero.id} loved it for {MATS[params.mat].purpose}, and {hero.pronoun()} kept it close.")

    world.para()
    other.memes["want_mat"] = 1.0
    world.say(f"Then {other.id} came near and asked to use the mat too.")
    world.say(f"{hero.id} felt a small tug of worry, because {hero.pronoun('possessive')} mat was the one thing {hero.pronoun()} did not want to lose.")

    world.para()
    world.say(f"But the old mat held a twist: {twist.reveal}.")
    world.say(f"That meant {twist.helps}, so {twist.outcome}.")

    hero.memes["peace"] = 1.0
    hero.memes["joy"] = 1.0
    other.memes["joy"] = 1.0
    world.para()
    world.say(f"{hero.id} smiled and moved over at once.")
    world.say(f"The two of them settled together on the mat, sharing the warm place as {world.setting.light} light fell around them.")
    world.say(f"And by the end, the mat was still there, but now it held two happy hearts instead of one lonely wish.")

    return world


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for mid, m in MATS.items():
        lines.append(asp.fact("mat", mid))
        lines.append(asp.fact("purpose", mid, m.purpose))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


ASP_RULES = r"""
shared(M) :- mat(M).
happy_end(M) :- shared(M).
twist_help(T) :- twist(T).
valid_story(P, M, T) :- place(P), mat(M), twist(T), happy_end(M), twist_help(T).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    m = world.facts["mat"]
    return [
        f"Write a short myth-like story about a {p.hero_type} and a {m.label}.",
        f"Tell a gentle tale where {p.name} must share a mat, but a twist changes everything.",
        f"Write a happy-ending myth with a mat, sharing, and a surprising reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    hero = f["hero"]
    mat = f["mat"]
    twist = f["twist"]
    return [
        QAItem(
            question=f"What was {p.name} trying to keep for {hero.pronoun('object')}self?",
            answer=f"{hero.pronoun('possessive').capitalize()} {mat.label} was the thing {p.name} wanted to keep close.",
        ),
        QAItem(
            question=f"What changed the problem in the story?",
            answer=f"The twist was that {twist.reveal}, which made sharing easy.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended happily, with both characters sharing the mat side by side.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mat?",
            answer="A mat is a flat thing you can sit, lie, or kneel on.",
        ),
        QAItem(
            question="Why do people share mats?",
            answer="People share mats when there is room for more than one person, or when sharing feels kind.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("meadow", "sleep", "girl", "Mira", "gentle", base_seed),
            StoryParams("riverbank", "picnic", "boy", "Arun", "kind", base_seed + 1),
            StoryParams("hut", "prayer", "queen", "Nyra", "quiet", base_seed + 2),
            StoryParams("garden", "dance", "sister", "Lila", "brave", base_seed + 3),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
