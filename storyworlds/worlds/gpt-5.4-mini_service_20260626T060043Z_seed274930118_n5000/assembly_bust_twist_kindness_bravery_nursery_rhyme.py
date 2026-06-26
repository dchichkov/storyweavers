#!/usr/bin/env python3
"""
A small storyworld about a nursery-rhyme assembly that can bust, then turn on
Kindness and Bravery with a gentle Twist.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    helper: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Build:
    id: str
    verb: str
    gerund: str
    mess: str
    bust: str
    twist: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    protects: set[str]
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "nursery": Place("the nursery", indoors=True, affords={"blocks", "paper", "string"}),
    "playroom": Place("the playroom", indoors=True, affords={"blocks", "paper", "string"}),
    "kitchen": Place("the kitchen", indoors=True, affords={"paper", "string"}),
}

BUILDS = {
    "blocks": Build(
        id="blocks",
        verb="build a little tower",
        gerund="building a little tower",
        mess="wobbly",
        bust="tipped over",
        twist="turned with a twist",
        zone="hands",
        keyword="blocks",
        tags={"blocks", "tower"},
    ),
    "paper": Build(
        id="paper",
        verb="make a paper crown",
        gerund="making a paper crown",
        mess="torn",
        bust="ripped",
        twist="folded with a twist",
        zone="hands",
        keyword="paper",
        tags={"paper", "crown"},
    ),
    "string": Build(
        id="string",
        verb="tie a bright string hoop",
        gerund="tying a bright string hoop",
        mess="snapped",
        bust="broke",
        twist="twisted with care",
        zone="hands",
        keyword="string",
        tags={"string", "hoop"},
    ),
}

FIXES = {
    "knot": Fix(
        id="knot",
        label="a neat knot",
        prep="tie in a neat knot",
        tail="made a neat little knot and held it tight",
        covers={"hands"},
        protects={"snapped", "broke"},
    ),
    "tape": Fix(
        id="tape",
        label="a strip of tape",
        prep="use a strip of tape",
        tail="used a strip of tape and made it stick",
        covers={"hands"},
        protects={"torn", "wobbly"},
    ),
    "brace": Fix(
        id="brace",
        label="a tiny brace",
        prep="add a tiny brace",
        tail="added a tiny brace and steadied the stack",
        covers={"hands"},
        protects={"wobbly", "snapped"},
    ),
}

CHAR_NAMES = ["Mia", "Leo", "Nina", "Owen", "Luna", "Ben", "Ivy", "Noah"]
TRAITS = ["tiny", "sweet", "bright", "cheery", "gentle", "spry"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    build: str
    name: str
    role: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A build is at risk when the place affords it and the break kind matches.
at_risk(P, B) :- affords(P, B), build(B).

% A fix is reasonable if it covers the active zone and protects the bust kind.
good_fix(B, F) :- at_risk(_, B), fix(F), covers(F, hands), protects(F, B).

valid_story(P, B) :- place(P), build(B), affords(P, B), good_fix(B, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for b in sorted(p.affords):
            lines.append(asp.fact("affords", pid, b))
    for bid, b in BUILDS.items():
        lines.append(asp.fact("build", bid))
        lines.append(asp.fact("bust_kind", bid, b.bust))
        lines.append(asp.fact("zone", bid, b.zone))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for c in sorted(f.covers):
            lines.append(asp.fact("covers", fid, c))
        for p in sorted(f.protects):
            lines.append(asp.fact("protects", fid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place, p in PLACES.items():
        for build in p.affords:
            b = BUILDS[build]
            if any(f for f in FIXES.values() if b.bust in f.protects and b.zone in f.covers):
                combos.append((place, build))
    return combos


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print(" only in clingo:", sorted(a - p))
    if p - a:
        print(" only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def choose_fix(build: Build) -> Optional[Fix]:
    for fix in FIXES.values():
        if build.bust in fix.protects and build.zone in fix.covers:
            return fix
    return None


def tell(place: Place, build: Build, hero_name: str, role: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=role))
    helper = world.add(Entity(id="Helper", kind="character", type="mother" if role == "boy" else "father"))
    project = world.add(Entity(
        id="Project",
        type=build.id,
        label=build.keyword,
        phrase=build.verb,
        owner=hero.id,
    ))

    # Setup
    world.say(
        f"At {place.name}, a {trait} little {role} named {hero_name} began an assembly."
    )
    world.say(
        f"{hero_name} loved {build.gerund}, and the room went soft with a nursery rhyme hum."
    )
    world.say(
        f"Their little {build.keyword} plan seemed merry and bright, like moonlight on a sill."
    )

    # Conflict
    world.para()
    hero.memes["hope"] = 1
    world.say(
        f"But the assembly grew wonky. One wrong wiggle, and the {build.keyword} would {build.bust}."
    )
    hero.memes["worry"] = 1
    world.say(
        f"{hero_name} saw the wobble and feared the whole thing might bust and tumble down."
    )
    hero.memes["bravery"] = 1
    world.say(
        f"Still, brave {hero_name} took a breath and tried a kinder way."
    )

    fix = choose_fix(build)
    if fix is None:
        raise StoryError("No reasonable fix exists for this build.")
    helper.memes["kindness"] = 1
    world.say(
        f"{helper.pronoun().capitalize()} smiled kindly and said, "
        f'"Let us {fix.prep}, and make the little part hold."'
    )

    # Resolution
    world.para()
    project.meters["stability"] = 1
    project.meters["done"] = 1
    hero.memes["joy"] = 1
    hero.memes["bravery"] = 1
    helper.memes["kindness"] = 1
    world.say(
        f"So they {fix.tail}. The twist was gentle, and the bust never came."
    )
    world.say(
        f"At last the {build.keyword} stood snug and sure, and {hero_name} laughed in delight."
    )
    world.say(
        f"In the quiet glow, kindness and bravery made the tiny assembly feel like a song."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        project=project,
        build=build,
        fix=fix,
        place=place,
        role=role,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story about an assembly that can bust, and where {f["hero"].id} learns kindness and bravery.',
        f"Tell a gentle story in {f['place'].name} where a little {f['role']} named {f['hero'].id} tries to {f['build'].verb} but saves it with a twist.",
        f'Write a short child-facing story that uses the words "assembly" and "bust" and ends with kindness helping the brave fix the problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    build = f["build"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to make in {f['place'].name}?",
            answer=f"{hero.id} was trying to {build.verb}. It started as a sweet little assembly.",
        ),
        QAItem(
            question=f"What problem almost happened to the {build.keyword} assembly?",
            answer=f"The assembly almost {build.bust}. That was the bust that made everyone worry.",
        ),
        QAItem(
            question=f"How did {hero.id} and the helper save the day?",
            answer=f"They used {fix.label} to steady the build. Kindness from {helper.id} and bravery from {hero.id} made the twist work.",
        ),
        QAItem(
            question=f"What did the ending feel like?",
            answer=f"The ending felt calm and happy. The little project stood safely, and the rhyme-like room turned warm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, caring, and helpful to someone else.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is being scared but still doing the helpful thing anyway.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a turn that changes what happens next in a surprising way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: assembly, bust, kindness, bravery, and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--build", choices=BUILDS)
    ap.add_argument("--name", choices=CHAR_NAMES)
    ap.add_argument("--role", choices=["girl", "boy"])
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
    if args.place and args.build:
        if (args.place, args.build) not in valid_combos():
            raise StoryError("No valid nursery-rhyme story matches that place and build.")
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              if args.build is None or c[1] == args.build]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, build = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHAR_NAMES)
    role = args.role or rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, build=build, name=name, role=role, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], BUILDS[params.build], params.name, params.role, params.trait)
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


CURATED = [
    StoryParams(place="nursery", build="blocks", name="Mia", role="girl", trait="cheery"),
    StoryParams(place="playroom", build="paper", name="Leo", role="boy", trait="bright"),
    StoryParams(place="kitchen", build="string", name="Ivy", role="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
