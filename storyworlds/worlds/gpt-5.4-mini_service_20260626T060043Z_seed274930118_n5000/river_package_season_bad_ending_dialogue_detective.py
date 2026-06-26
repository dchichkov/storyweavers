#!/usr/bin/env python3
"""
storyworlds/worlds/river_package_season_bad_ending_dialogue_detective.py
=======================================================================

A small detective-story world about a river, a package, and the changing season.

Premise:
- A curious detective follows a package that should have arrived by the river.
- The season changes the river's level and the clues that remain visible.
- Dialogue matters: witnesses speak, the detective asks questions, and the answer
  turns the case.
- The ending is bad on purpose: the package is lost, ruined, or cannot be saved.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    season: str
    river_state: str
    affords: set[str] = field(default_factory=set)


@dataclass
class PackageKind:
    id: str
    label: str
    phrase: str
    risk: str
    good_season: set[str]
    bad_season: set[str]
    can_ruin_by: set[str]


@dataclass
class StoryParams:
    setting: str
    package: str
    season: str
    detective: str
    witness: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
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


SETTINGS = {
    "bridge": Setting(place="the old bridge by the river", season="spring", river_state="high", affords={"speak", "search"}),
    "dock": Setting(place="the dock", season="summer", river_state="calm", affords={"speak", "search"}),
    "bank": Setting(place="the muddy river bank", season="autumn", river_state="swollen", affords={"speak", "search"}),
    "ferry": Setting(place="the ferry landing", season="winter", river_state="icy", affords={"speak", "search"}),
}

PACKAGES = {
    "paper": PackageKind(
        id="paper",
        label="paper package",
        phrase="a paper-wrapped package tied with blue string",
        risk="soaked",
        good_season={"summer"},
        bad_season={"spring", "autumn", "winter"},
        can_ruin_by={"water"},
    ),
    "cloth": PackageKind(
        id="cloth",
        label="cloth package",
        phrase="a cloth-wrapped package with a stamped seal",
        risk="stained",
        good_season={"spring", "summer"},
        bad_season={"winter"},
        can_ruin_by={"mud"},
    ),
    "wood": PackageKind(
        id="wood",
        label="wooden package",
        phrase="a small wooden package with a brass latch",
        risk="sun-cracked",
        good_season={"autumn", "winter"},
        bad_season={"summer"},
        can_ruin_by={"heat"},
    ),
}

DETECTIVES = ["Mara", "Ivy", "Noah", "Theo", "Nina", "June"]
WITNESSES = ["boatman", "fisher", "shopkeeper", "porter", "guard", "old woman"]


def _story_setting(place: str, season: str) -> Setting:
    base = SETTINGS[place]
    river_state = {
        "spring": "swift and high",
        "summer": "low and bright",
        "autumn": "cold and swollen",
        "winter": "dark and icy",
    }[season]
    return Setting(place=base.place, season=season, river_state=river_state, affords=set(base.affords))


def risk_reason(pkg: PackageKind, season: str) -> bool:
    return season in pkg.bad_season


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.package and args.season:
        pkg = PACKAGES[args.package]
        if not risk_reason(pkg, args.season):
            raise StoryError(
                f"(No story: a {pkg.label} is not endangered enough in {args.season}; "
                f"this world needs a bad turn, not a safe errand.)"
            )
    combos = [
        (place, package, season)
        for place in SETTINGS
        for package in PACKAGES
        for season in {"spring", "summer", "autumn", "winter"}
        if risk_reason(PACKAGES[package], season)
    ]
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.package:
        combos = [c for c in combos if c[1] == args.package]
    if args.season:
        combos = [c for c in combos if c[2] == args.season]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, package, season = rng.choice(sorted(combos))
    detective = args.detective or rng.choice(DETECTIVES)
    witness = args.witness or rng.choice(WITNESSES)
    return StoryParams(setting=place, package=package, season=season, detective=detective, witness=witness)


def tell(setting: Setting, package: PackageKind, detective_name: str, witness_role: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type="detective", label="the detective"))
    witness = world.add(Entity(id=witness_role, kind="character", type=witness_role, label=f"the {witness_role}"))
    pkg = world.add(Entity(
        id="package",
        kind="thing",
        type=package.id,
        label=package.label,
        phrase=package.phrase,
        owner="sender",
        caretaker=detective.id,
    ))

    detective.memes["curiosity"] = 1.0
    witness.memes["nervous"] = 1.0

    world.say(
        f"{detective.id} was a detective who liked small clues, quiet footsteps, and cases that began by the river."
    )
    world.say(
        f"One day, a {package.label} was supposed to arrive at {setting.place}, but nobody could say where it went."
    )

    world.para()
    world.say(
        f"The season was {setting.season}, and the river was {setting.river_state}."
    )
    world.say(
        f'{detective.id} looked at the water and said, "If the package passed here, the river might have taken part of the answer."'
    )
    world.say(
        f'The {witness_role} whispered, "{witness_role.title()} saw it near the bank, but it was already too late."'
    )

    world.para()
    detective.memes["tense"] = 1.0
    if setting.season in {"spring", "autumn", "winter"}:
        pkg.meters["water"] = 1.0
    if setting.season in {"autumn", "winter"}:
        pkg.meters["mud"] = 1.0

    world.say(
        f'{detective.id} asked, "Was it safe?"'
    )
    world.say(
        f'The {witness_role} answered, "No. The river rose, the path slipped away, and the package went out of sight."'
    )

    world.para()
    if setting.season == "winter":
        ending = "The detective found only a torn string on the ice, and the case ended with the package lost forever."
    elif setting.season == "autumn":
        ending = "The detective found the package stuck in the mud, but its papers were ruined and the delivery was a failure."
    elif setting.season == "spring":
        ending = "The detective saw the package sweep under the bridge, and by the time help came, the river had swallowed it."
    else:
        ending = "The detective found the empty spot where the package had been, but the trail had already vanished into the sun."
    world.say(ending)

    world.facts.update(
        detective=detective,
        witness=witness,
        package=pkg,
        package_kind=package,
        setting=setting,
        bad_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child that includes a river, a package, and the season {f["setting"].season}.',
        f'Tell a mystery story where {f["detective"].id} asks a witness about a package by the river and the ending goes badly.',
        f'Write a simple dialogue-heavy story about a lost package near {f["setting"].place} in {f["setting"].season}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"].id
    wit = f["witness"].id
    setting = f["setting"]
    pkg = f["package_kind"]
    return [
        QAItem(
            question=f"Who was trying to solve the mystery by the river?",
            answer=f"{det} was the detective trying to solve the mystery at {setting.place}.",
        ),
        QAItem(
            question=f"What kind of package was the detective looking for?",
            answer=f"The detective was looking for {pkg.phrase}.",
        ),
        QAItem(
            question=f"What did the witness say happened to the package?",
            answer=f"The {wit} said the package was already gone when the river rose and the path slipped away.",
        ),
        QAItem(
            question=f"Why did the case end badly?",
            answer=f"It ended badly because the river and the season made the package impossible to save, so the detective could only find a ruined clue or an empty place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    season = world.facts["setting"].season
    pkg = world.facts["package_kind"]
    qa = [
        QAItem(
            question="What is a river?",
            answer="A river is a long stream of moving water that flows across the land.",
        ),
        QAItem(
            question="Why can a package get ruined near water?",
            answer="A package can get ruined near water because paper, cloth, or papers inside it may soak up the water and fall apart.",
        ),
        QAItem(
            question="What changes in a season?",
            answer="A season changes the weather, the light, and sometimes how full or cold a river looks.",
        ),
    ]
    if season == "winter":
        qa.append(QAItem(question="What is icy water like?", answer="Icy water is very cold and can freeze into hard slick patches."))
    if pkg.id == "paper":
        qa.append(QAItem(question="Why is paper weak in wet weather?", answer="Paper gets soft and bends or tears when it gets wet."))
    return qa


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for season in {"spring", "summer", "autumn", "winter"}:
        lines.append(asp.fact("season", season))
    for pkg in PACKAGES.values():
        lines.append(asp.fact("package", pkg.id))
        for s in sorted(pkg.bad_season):
            lines.append(asp.fact("bad_for", pkg.id, s))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,P) :- season(S), package(P), bad_for(P,S).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((s, p) for s in {"spring", "summer", "autumn", "winter"} for p in PACKAGES if risk_reason(PACKAGES[p], s))
    cl = asp_valid_stories()
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} valid stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("python:", py)
    print("clingo:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: river, package, season, dialogue, bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--package", choices=PACKAGES)
    ap.add_argument("--season", choices=["spring", "summer", "autumn", "winter"])
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--witness", choices=WITNESSES)
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


def generate(params: StoryParams) -> StorySample:
    setting = _story_setting(params.setting, params.season)
    world = tell(setting, PACKAGES[params.package], params.detective, params.witness)
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
    StoryParams(setting="bridge", package="paper", season="spring", detective="Mara", witness="boatman"),
    StoryParams(setting="bank", package="cloth", season="autumn", detective="Ivy", witness="fisher"),
    StoryParams(setting="ferry", package="wood", season="winter", detective="June", witness="guard"),
]


def resolve_curated(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [p for p in CURATED if (not args.setting or p.setting == args.setting) and (not args.package or p.package == args.package) and (not args.season or p.season == args.season)]
    if not choices:
        raise StoryError("(No curated story matches the given options.)")
    p = rng.choice(choices)
    if args.detective:
        p.detective = args.detective
    if args.witness:
        p.witness = args.witness
    return p


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.all:
        raise StoryError("resolve_params() is not used with --all")
    if args.setting and args.package and args.season:
        if not risk_reason(PACKAGES[args.package], args.season):
            raise StoryError(
                f"(No story: {PACKAGES[args.package].label} is not in danger in {args.season}; "
                f"this needs a bad ending.)"
            )
    settings = [args.setting] if args.setting else list(SETTINGS)
    packages = [args.package] if args.package else list(PACKAGES)
    seasons = [args.season] if args.season else ["spring", "summer", "autumn", "winter"]
    combos = [(s, p, se) for s in settings for p in packages for se in seasons if risk_reason(PACKAGES[p], se)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, package, season = rng.choice(sorted(combos))
    detective = args.detective or rng.choice(DETECTIVES)
    witness = args.witness or rng.choice(WITNESSES)
    return StoryParams(setting=setting, package=package, season=season, detective=detective, witness=witness)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid (season, package) combinations:\n")
        for season, package in stories:
            print(f"  {season:8} {package}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            if args.setting and p.setting != args.setting:
                continue
            if args.package and p.package != args.package:
                continue
            if args.season and p.season != args.season:
                continue
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective}: {p.package} in {p.season} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
