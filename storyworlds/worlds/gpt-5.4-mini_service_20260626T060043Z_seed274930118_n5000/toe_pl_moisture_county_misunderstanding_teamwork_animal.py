#!/usr/bin/env python3
"""
A small animal-story world about a county day, a moisture mix-up, and teamwork.

Seed words: toe-pl, moisture, county
Style: Animal Story
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

ANIMALS = ["fox", "badger", "rabbit", "duck", "goat", "raccoon", "mouse", "otter"]
NAMES = ["Pip", "Milo", "Nina", "Toby", "Clover", "Ruby", "Penny", "Junie"]
COUNTY_PLACES = [
    "the county barn",
    "the county orchard",
    "the county lane",
    "the county market shed",
]
MOISTURE_KINDS = ["dew", "rain", "mud", "pond-water"]
HELP_ITEMS = ["dry towel", "big leaf", "clean cloth", "warm blanket"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    species: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    wears: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords_moisture: bool = True


@dataclass
class Mood:
    misunderstanding: bool = True
    teamwork: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_species: str
    helper_name: str
    helper_species: str
    moisture: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mood: Mood) -> None:
        self.setting = setting
        self.mood = mood
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


def aspiration_text(hero: Entity, moisture: str) -> str:
    return f"{hero.id} loved exploring after {moisture} touched the grass"


def intro(world: World, hero: Entity, helper: Entity, moisture: str) -> None:
    world.say(
        f"{hero.id} was a little {hero.species} who lived near {world.setting.place}."
    )
    world.say(
        f"{helper.id} was a friendly {helper.species} who liked to help."
    )
    world.say(
        f"{aspiration_text(hero, moisture)}, and the day always felt exciting when the ground was soft."
    )


def setup_problem(world: World, hero: Entity, helper: Entity, moisture: str) -> Entity:
    prize = world.add(Entity(
        id="toe-pl",
        kind="thing",
        species="bundle",
        label="toe-pl basket",
        owner=hero.id,
    ))
    hero.meters[moisture] = 1.0
    hero.memes["hope"] = 1.0
    world.say(
        f"That morning, {hero.id} carried a small toe-pl basket to {world.setting.place}."
    )
    world.say(
        f"It held dry apples, and {hero.id} wanted to keep it neat."
    )
    world.facts["prize"] = prize
    return prize


def misunderstanding(world: World, hero: Entity, helper: Entity, prize: Entity, moisture: str) -> None:
    hero.meters[moisture] = 2.0
    helper.memes["worry"] = 1.0
    world.para()
    world.say(
        f"Then a puff of {moisture} drifted in, and {hero.id}'s paws got damp."
    )
    world.say(
        f"{helper.id} saw the wet paws beside the toe-pl basket and thought {hero.id} had dropped water into it."
    )
    hero.memes["hurt"] = 1.0
    world.say(
        f"{hero.id} frowned, because that was not what happened at all."
    )


def teamwork(world: World, hero: Entity, helper: Entity, prize: Entity, moisture: str) -> None:
    world.para()
    world.say(
        f"Before the mix-up could grow, {helper.id} called the others over."
    )
    world.say(
        f"One animal found a dry towel, another brought a big leaf, and {helper.id} held the basket still."
    )
    hero.memes["calm"] = 1.0
    helper.memes["teamwork"] = 1.0
    prize.meters["dry"] = 1.0
    hero.meters["moisture"] = 0.0
    world.say(
        f"Together they wiped away the moisture, and the toe-pl basket stayed clean."
    )
    world.say(
        f"{hero.id} smiled and showed that the apples were safe all along."
    )
    world.say(
        f"The helpers laughed, because working together was easier than guessing."
    )


def tell(params: StoryParams) -> World:
    world = World(Setting(params.place), Mood())
    hero = world.add(Entity(id=params.hero_name, kind="character", species=params.hero_species))
    helper = world.add(Entity(id=params.helper_name, kind="character", species=params.helper_species))
    prize = setup_problem(world, hero, helper, params.moisture)
    intro(world, hero, helper, params.moisture)
    misunderstanding(world, hero, helper, prize, params.moisture)
    teamwork(world, hero, helper, prize, params.moisture)
    world.facts.update(hero=hero, helper=helper, prize=prize, moisture=params.moisture)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write an animal story set in the county about {world.facts['moisture']} and teamwork.",
        "Tell a gentle story where a misunderstanding gets fixed when the animals work together.",
        "Make the story child-friendly, concrete, and warm, with a county setting and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    prize = world.facts["prize"]
    moisture = world.facts["moisture"]
    return [
        QAItem(
            question=f"Why did {helper.id} think {hero.id} had made a mess?",
            answer=f"{helper.id} saw {hero.id}'s wet paws beside the toe-pl basket and guessed that {moisture} had gotten inside it.",
        ),
        QAItem(
            question="What fixed the misunderstanding?",
            answer=f"The animals worked together, used a dry towel and a big leaf, and checked the basket carefully.",
        ),
        QAItem(
            question=f"What stayed safe at the end of the story?",
            answer=f"The toe-pl basket stayed clean, and the apples inside it were still safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is moisture?",
            answer="Moisture is a little bit of wetness on things like grass, paws, or leaves.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people or animals help each other and do a job together.",
        ),
        QAItem(
            question="What is a county?",
            answer="A county is a part of a state or country, and it can have towns, roads, farms, and barns.",
        ),
    ]


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {ent.id} ({ent.species}) {' '.join(bits)}")
    return "\n".join(out)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about county moisture and teamwork.")
    ap.add_argument("--place", choices=COUNTY_PLACES)
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
    place = args.place or rng.choice(COUNTY_PLACES)
    hero_species = rng.choice(ANIMALS)
    helper_species = rng.choice([a for a in ANIMALS if a != hero_species])
    hero_name = rng.choice(NAMES)
    helper_name = rng.choice([n for n in NAMES if n != hero_name])
    moisture = rng.choice(MOISTURE_KINDS)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_species=hero_species,
        helper_name=helper_name,
        helper_species=helper_species,
        moisture=moisture,
    )


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


def asp_facts() -> str:
    return "\n".join(
        [
            'setting(county).',
            'feature(misunderstanding).',
            'feature(teamwork).',
            'word("toe-pl").',
            'word("moisture").',
            'word("county").',
        ]
    )


ASP_RULES = r"""
valid_story(county, misunderstanding, teamwork) :- setting(county), feature(misunderstanding), feature(teamwork).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    vals = set(asp.atoms(model, "valid_story"))
    expected = {("county", "misunderstanding", "teamwork")}
    if vals == expected:
        print("OK: ASP facts and Python world agree.")
        return 0
    print("MISMATCH:", vals, expected)
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples.append(generate(resolve_params(args, random.Random(base_seed))))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### story {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
