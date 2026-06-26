#!/usr/bin/env python3
"""
A fairy-tale storyworld about a swamp, bravery, and a mystery to solve.

A small hero arrives at a swamp where something puzzling has happened: the
lantern path has gone dark, a little creature has vanished, or a bridge sign is
missing. The hero must be brave, ask careful questions, and follow clues in the
mud, reeds, and mist until the mystery is solved with a gentle, storybook turn.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "woman", "witch", "fairy"}
        male = {"boy", "king", "prince", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    features: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    title: str
    clue_word: str
    cause: str
    solution: str
    risk: str
    revealed_by: str
    features: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str] = field(default_factory=set)
    protects: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.steps: list[str] = []

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
    "moon_swamp": Setting(place="the moonlit swamp", features={"swamp", "mist", "reeds", "moonlight"}),
    "elder_swamp": Setting(place="the elder swamp", features={"swamp", "old_tree", "dugout"}),
    "green_swamp": Setting(place="the green swamp", features={"swamp", "lilies", "frog", "mist"}),
}

MYSTERIES = {
    "silent_lantern": Mystery(
        id="silent_lantern",
        title="the silent lantern",
        clue_word="lantern",
        cause="a dragonfly had covered the lantern glass with sticky pollen",
        solution="the pollen was wiped away with a soft moss cloth",
        risk="the path would stay dark and hard to follow",
        revealed_by="a little sparkle on the reeds",
        features={"swamp", "light", "clue", "mist"},
    ),
    "missing_song": Mystery(
        id="missing_song",
        title="the missing song",
        clue_word="song",
        cause="a shy frog had hidden under a lily leaf to rest",
        solution="the frog was found and asked to sing again",
        risk="the swamp would feel lonely and quiet",
        revealed_by="a ripple in the water",
        features={"swamp", "frog", "clue", "voice"},
    ),
    "lost_key": Mystery(
        id="lost_key",
        title="the lost key",
        clue_word="key",
        cause="the key had slipped into a hollow log beside the swamp",
        solution="the hero reached into the log and lifted the key out",
        risk="the little gate would not open",
        revealed_by="a ring of mud near the log",
        features={"swamp", "gate", "clue", "mud"},
    ),
}

TOOLS = {
    "moss_cloth": Tool(
        id="moss_cloth",
        label="moss cloth",
        phrase="a soft moss cloth",
        helps_with={"silent_lantern"},
        protects={"mud"},
    ),
    "little_lamp": Tool(
        id="little_lamp",
        label="little lamp",
        phrase="a little lamp with a bright smile of light",
        helps_with={"silent_lantern"},
        protects={"mist"},
    ),
    "reed_stick": Tool(
        id="reed_stick",
        label="reed stick",
        phrase="a reed stick for pointing at clues",
        helps_with={"missing_song", "lost_key"},
        protects=set(),
    ),
    "tiny_boat": Tool(
        id="tiny_boat",
        label="tiny boat",
        phrase="a tiny boat with a quiet oar",
        helps_with={"missing_song", "lost_key"},
        protects={"water"},
    ),
}

HERO_NAMES = ["Luna", "Milo", "Tessa", "Pip", "Nora", "Rory", "Elin", "Ari"]
HELPERS = ["a kind fairy", "an old heron", "a wise frog", "a lantern sprite"]
TRAITS = ["brave", "gentle", "curious", "steadfast", "bright-eyed"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale swamp storyworld with bravery and a mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "neutral"])
    ap.add_argument("--helper", choices=range(len(HELPERS)), type=int)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    name = args.name or rng.choice(HERO_NAMES)
    gender = args.gender or rng.choice(["girl", "boy", "neutral"])
    helper = HELPERS[args.helper] if args.helper is not None else rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, helper=helper, trait=trait)


def pronounce_name(name: str, gender: str) -> str:
    return name


def pronoun(gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if gender == "boy":
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def story_intro(world: World, hero: Entity, helper: str, mystery: Mystery) -> None:
    world.say(f"In {world.setting.place}, there lived a {hero.memes['trait_word']} hero named {hero.id}.")
    world.say(f"{hero.pronoun().capitalize()} loved to listen to {helper} and to notice small things others missed.")
    world.say(f"One day, a mystery grew near the water: {mystery.title}.")


def story_turn(world: World, hero: Entity, mystery: Mystery, tool: Tool) -> None:
    hero.memes["bravery"] += 1
    hero.memes["curiosity"] += 1
    world.para()
    world.say(f"{hero.id} did not run from the swampy fog. Instead, {hero.pronoun()} took a steady breath and stepped closer.")
    world.say(f"Near the reeds, {hero.pronoun('subject')} found {tool.phrase} and followed the clue of {mystery.revealed_by}.")
    world.say(f"The clue led {hero.pronoun('object')} toward the place where the mystery could be solved.")


def story_resolution(world: World, hero: Entity, mystery: Mystery, tool: Tool) -> None:
    hero.memes["joy"] += 1
    world.para()
    world.say(f"At last, {hero.id} solved {mystery.title}: {mystery.cause}.")
    world.say(mystery.solution.capitalize() + ".")
    world.say(f"The swamp felt peaceful again, and {hero.id} stood a little taller, brave as a candle in the mist.")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"distance": 0.0},
        memes={"trait_word": params.trait, "bravery": 0.0, "curiosity": 0.0, "joy": 0.0},
    ))
    world.facts["hero"] = hero
    world.facts["helper"] = params.helper
    world.facts["mystery"] = mystery
    tool = next((t for t in TOOLS.values() if mystery.id in t.helps_with), list(TOOLS.values())[0])
    world.facts["tool"] = tool
    story_intro(world, hero, params.helper, mystery)
    story_turn(world, hero, mystery, tool)
    story_resolution(world, hero, mystery, tool)
    return world


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in SETTINGS:
        for mystery in MYSTERIES:
            combos.append((setting, mystery))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    hero: Entity = f["hero"]
    return [
        f'Write a fairy-tale story about a brave child in a swamp who solves the mystery of "{mystery.title}".',
        f"Tell a gentle swamp tale where {hero.id} stays brave, follows a clue, and discovers why the {mystery.clue_word} went missing.",
        f"Write a child-friendly story in a misty swamp about courage, clues, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a {hero.memes['trait_word']} and brave little hero in the swamp.",
        ),
        QAItem(
            question=f"What mystery did {hero.id} solve?",
            answer=f"{hero.id} solved {mystery.title}, which was the mystery of the {mystery.clue_word}.",
        ),
        QAItem(
            question=f"What helped {hero.id} follow the clues?",
            answer=f"{tool.phrase} helped {hero.id} follow the clues through the swampy mist.",
        ),
        QAItem(
            question=f"Why did the mystery matter in the story?",
            answer=f"It mattered because {mystery.risk}, so the hero had to be brave and find the answer.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a swamp?",
            answer="A swamp is a wet place with muddy ground, water, reeds, and often mist or trees growing nearby.",
        ),
        QAItem(
            question="Why does bravery matter in a mystery story?",
            answer="Bravery matters because a character may need to keep going even when the clues are strange or the path feels scary.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that characters try to understand by looking for clues.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(moon_swamp;elder_swamp;green_swamp).
mystery(silent_lantern;missing_song;lost_key).

valid(Setting,Mystery) :- setting(Setting), mystery(Mystery).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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


CURATED = [
    StoryParams(setting="moon_swamp", mystery="silent_lantern", name="Luna", gender="girl", helper=HELPERS[0], trait="brave"),
    StoryParams(setting="elder_swamp", mystery="missing_song", name="Pip", gender="boy", helper=HELPERS[2], trait="curious"),
    StoryParams(setting="green_swamp", mystery="lost_key", name="Tessa", gender="girl", helper=HELPERS[1], trait="steadfast"),
]


def explain_rejection(setting: str, mystery: str) -> str:
    return f"(No story: the swamp tale needs a fitting mystery, and {setting} with {mystery} was not selected.)"


def resolve_and_generate(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    params.seed = args.seed
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible swamp story combos:\n")
        for c in combos:
            print(f"  {c[0]}  {c[1]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            sample = resolve_and_generate(args, rng)
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
            header = f"### {p.name}: {p.setting} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
