#!/usr/bin/env python3
"""
Animal-story world: a blarney-filled fortyniner tale with a small comic turn.

A seed tale imagined for this world:
---
A scruffy coyote named Cork was a fortyniner in a tiny desert camp. He loved shiny pebbles,
but he loved talking even more. Every morning he told long, silly blarney stories about
how he could hear gold singing under the rocks.

One day Cork found a stubborn old mule named Dot. Dot had a wagon of water cans that had
gotten stuck in a sandy ditch. Cork wanted to chase the gold right away, but Dot asked for
help first. Cork tried to impress her with more blarney, but the wagon did not budge.

So Cork laughed, put down his pretend miner's spoon, and used a rope to pull. Dot helped,
the wagon rolled free, and Cork found that one honest tug was worth ten tall tales.
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

FORTYNINER = "fortyniner"
BLARNEY = "blarney"


@dataclass
class Animal:
    id: str
    kind: str = "animal"
    species: str = "animal"
    name: str = ""
    adjective: str = ""
    role: str = ""
    nickname: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    terrain: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Object:
    id: str
    label: str
    kind: str = "thing"
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    treasure: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
    "camp": Setting(place="the desert camp", terrain="sand", affords={"dig", "pull"}),
    "gulch": Setting(place="the little gulch", terrain="sand", affords={"dig", "pull"}),
    "ridge": Setting(place="the windy ridge", terrain="rock", affords={"talk", "pull"}),
}

ANIMALS = {
    "cork": ("coyote", "scruffy", "miner"),
    "dot": ("mule", "sturdy", "helper"),
    "pip": ("raven", "shiny", "trickster"),
    "mara": ("goat", "bright-eyed", "listener"),
}

TREASURES = {
    "pebble": ("one shiny pebble", "shiny pebble"),
    "pan": ("a dented gold pan", "gold pan"),
    "map": ("a treasure map with a coffee stain", "treasure map"),
}

CURATED = [
    StoryParams(place="camp", hero="cork", helper="dot", treasure="pan"),
    StoryParams(place="gulch", hero="cork", helper="pip", treasure="pebble"),
    StoryParams(place="ridge", hero="mara", helper="dot", treasure="map"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal-story world: a fortyniner and a little blarney lead to a comic fix."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--helper", choices=ANIMALS)
    ap.add_argument("--treasure", choices=TREASURES)
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
    if args.helper and args.hero and args.helper == args.hero:
        raise StoryError("The hero and helper should be different animals.")
    choices = list(SETTINGS)
    if args.place:
        choices = [args.place]
    place = rng.choice(choices)
    hero = args.hero or rng.choice([k for k in ANIMALS if k != "dot"])
    helper = args.helper or rng.choice([k for k in ANIMALS if k != hero])
    treasure = args.treasure or rng.choice(list(TREASURES))
    return StoryParams(place=place, hero=hero, helper=helper, treasure=treasure)


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


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero_species, hero_adj, hero_role = ANIMALS[params.hero]
    helper_species, helper_adj, helper_role = ANIMALS[params.helper]
    treasure_phrase, treasure_label = TREASURES[params.treasure]

    hero = world.add(Animal(
        id=params.hero,
        species=hero_species,
        adjective=hero_adj,
        role=hero_role,
        nickname=FORTYNINER,
        meters={"dust": 0.0},
        memes={"joy": 0.0, "pride": 1.0, "blarney": 2.0},
    ))
    helper = world.add(Animal(
        id=params.helper,
        species=helper_species,
        adjective=helper_adj,
        role=helper_role,
        meters={"dust": 0.0, "tired": 0.0},
        memes={"patience": 1.0, "amusement": 0.0},
    ))
    treasure = world.add(Object(
        id=params.treasure,
        label=treasure_label,
        phrase=treasure_phrase,
        owner=hero.id,
        meters={"stuck": 1.0},
    ))

    hero.memes["love_gold"] = 1.0
    world.say(f"{hero.name or hero.id.capitalize()} was a {hero.adjective} {hero.species} and a {FORTYNINER} at {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} loved shiny things and even more {BLARNEY}, which made every story sound bigger than a wagon wheel.")
    world.say(f"One bright morning, {hero.id} spotted {treasure.phrase} near a sandy ditch.")
    world.para()
    world.say(f"{hero.id} wanted to chase the gold right away, but {helper.id} was there with a stuck water wagon.")
    world.say(f"{helper.id} asked for help first, while {hero.id} tried a big round of {BLARNEY} about hidden riches.")
    hero.memes["blarney"] += 1.0
    helper.memes["amusement"] += 1.0
    world.say(f"The tale was funny, but the wagon still would not move.")
    world.para()
    hero.memes["humor"] = 1.0
    hero.memes["kindness"] = 1.0
    helper.meters["tired"] += 1.0
    world.say(f"At last {hero.id} laughed, put down a pretend miner's spoon, and wrapped a rope around the wheel.")
    world.say(f"With one honest pull, the wagon rolled free, and {helper.id} let out a surprised snort of relief.")
    world.say(f"Then {hero.id} found that a helpful tug felt better than ten tall tales, and the shiny pebble waited for later.")
    world.facts.update(
        hero=hero,
        helper=helper,
        treasure=treasure,
        setting=setting,
        treasure_phrase=treasure_phrase,
        treasure_label=treasure_label,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a young child about a {FORTYNINER} who likes {BLARNEY} and learns to help a friend first.',
        f"Tell a funny story where {f['hero'].id} the {f['hero'].species} sees {f['treasure_phrase']} but stops to help {f['helper'].id}.",
        f"Write a gentle desert camp tale with a comic boast, a stuck wagon, and a happy pull free.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    treasure = f["treasure"]
    return [
        QAItem(
            question=f"Who was the fortyniner in the story?",
            answer=f"{hero.id} was the {FORTYNINER}. {hero.id} loved shiny things and liked to tell blarney-filled stories."
        ),
        QAItem(
            question=f"What problem did {helper.id} have at the start?",
            answer=f"{helper.id} had a wagon of water cans stuck in a sandy ditch, so {helper.id} needed help."
        ),
        QAItem(
            question=f"What changed after {hero.id} stopped boasting?",
            answer=f"{hero.id} put down the pretend miner's spoon, pulled with a rope, and the wagon rolled free."
        ),
        QAItem(
            question=f"Did the story end with {treasure.label} being used right away?",
            answer=f"No. The shiny {treasure.label} waited for later, because helping {helper.id} came first."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fortyniner?",
            answer="A fortyniner is a miner or treasure-hunter who looks for gold."
        ),
        QAItem(
            question="What is blarney?",
            answer="Blarney is smooth, playful talk that tries to charm people, often with a bit of exaggeration."
        ),
        QAItem(
            question="Why can a sandy ditch be hard to cross?",
            answer="Sand can slide under wheels and feet, so a wagon or cart can get stuck and need a strong pull."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        if isinstance(e, Animal):
            lines.append(f"  {e.id:8} animal={e.species} meters={e.meters} memes={e.memes}")
        else:
            lines.append(f"  {e.id:8} thing={e.label} meters={e.meters}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story q&a ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world q&a ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
% Declarative twin for the tiny reasonableness gate.
different(A,B) :- animal(A), animal(B), A != B.
valid_story(Place, Hero, Helper, Treasure) :- setting(Place), animal(Hero), animal(Helper), thing(Treasure), Hero != Helper.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for key in ANIMALS:
        lines.append(asp.fact("animal", key))
    for key in TREASURES:
        lines.append(asp.fact("thing", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_asp_summary() -> str:
    return "ASP mode is available for parity scaffolding, but this world uses Python gating."


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(build_asp_summary())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_combo(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
