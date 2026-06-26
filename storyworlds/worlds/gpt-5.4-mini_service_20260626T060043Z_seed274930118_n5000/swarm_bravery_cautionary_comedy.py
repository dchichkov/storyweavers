#!/usr/bin/env python3
"""
storyworlds/worlds/swarm_bravery_cautionary_comedy.py
======================================================

A small storyworld about a silly swarm, a brave child, and a cautionary turn
that ends with a funny, safe solution.

Premise:
- A child spots a swarm of tiny creatures in a public place.
- Bravery pushes the child forward.
- Cautionary worry keeps the situation from becoming foolishly dangerous.
- A gentle helper figure offers a comic, sensible fix.

The world is intentionally small: one location, one swarm, one brave choice,
one cautionary warning, and one playful resolution.
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    indoors: bool = False


@dataclass
class Swarm:
    id: str
    label: str
    kind: str
    size_word: str
    sound: str
    risk: str
    caution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    swarm_active: bool = False

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
    "garden": Setting(place="the garden"),
    "playground": Setting(place="the playground"),
    "market": Setting(place="the market"),
    "yard": Setting(place="the yard"),
}

SWARMS = {
    "bees": Swarm(
        id="bees",
        label="a swarm of bees",
        kind="bees",
        size_word="buzzing",
        sound="buzz-buzz-buzz",
        risk="stings",
        caution="keep still and step back slowly",
        tags={"swarm", "buzz", "bee"},
    ),
    "butterflies": Swarm(
        id="butterflies",
        label="a swarm of butterflies",
        kind="butterflies",
        size_word="fluttering",
        sound="flaaap-flaaap",
        risk="a very silly nose tickle",
        caution="move gently so they can flutter away",
        tags={"swarm", "flutter"},
    ),
    "ducklings": Swarm(
        id="ducklings",
        label="a swarm of ducklings",
        kind="ducklings",
        size_word="waddling",
        sound="peep-peep-peep",
        risk="a lot of splashing",
        caution="walk around them and let their parent lead",
        tags={"swarm", "cute"},
    ),
}

HERO_NAMES = ["Mina", "Toby", "Nia", "Pip", "Lola", "Ezra", "Hugo", "June"]
ADULT_NAMES = ["Mom", "Dad", "Auntie", "Uncle", "Grandma", "Grandpa"]
TRAITS = ["brave", "careful", "curious", "silly", "cheerful"]

ASP_RULES = r"""
swarm_kind(bees).
swarm_kind(butterflies).
swarm_kind(ducklings).

setting(garden).
setting(playground).
setting(market).
setting(yard).

safe_fix(A) :- swarm_kind(A).
cautionary(A) :- safe_fix(A).
bravery(A) :- safe_fix(A).
valid_story(S, A) :- setting(S), swarm_kind(A).
"""


@dataclass
class StoryParams:
    setting: str
    swarm: str
    name: str
    adult: str
    trait: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SWARMS:
        lines.append(asp.fact("swarm_kind", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def world_reasonable(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.swarm not in SWARMS:
        raise StoryError("Unknown swarm.")
    if not params.name:
        raise StoryError("Missing hero name.")
    if not params.adult:
        raise StoryError("Missing adult helper name.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic bravery-and-caution swarm storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--swarm", choices=SWARMS)
    ap.add_argument("--name")
    ap.add_argument("--adult", choices=ADULT_NAMES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    swarm = args.swarm or rng.choice(list(SWARMS))
    name = args.name or rng.choice(HERO_NAMES)
    adult = args.adult or rng.choice(ADULT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, swarm=swarm, name=name, adult=adult, trait=trait)


def make_world(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.setting])
    hero = world.add(Entity(id="hero", kind="character", type="child", label=params.name))
    adult = world.add(Entity(id="adult", kind="character", type="adult", label=params.adult))
    swarm = world.add(Entity(id="swarm", kind="thing", type=params.swarm, label=SWARMS[params.swarm].label, plural=True))

    hero.memes["bravery"] = 1.0
    hero.memes["caution"] = 0.5
    adult.memes["caution"] = 1.0
    world.facts.update(hero=hero, adult=adult, swarm=swarm, params=params)
    return world


def tell_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    adult: Entity = world.facts["adult"]
    swarm: Entity = world.facts["swarm"]
    params: StoryParams = world.facts["params"]
    sdef = SWARMS[params.swarm]

    world.say(
        f"{params.name} was a {params.trait} little child who loved exploring {world.setting.place}."
    )
    world.say(
        f"One day, {params.name} heard {sdef.sound} and spotted {sdef.label} dancing near the path."
    )
    world.para()
    world.say(
        f"{params.name} took a deep breath and tried to be brave. "
        f"{hero.pronoun().capitalize()} wanted to look closer, because bravery felt exciting."
    )
    world.say(
        f"But {params.adult} raised a hand and gave a cautionary smile. "
        f"'{sdef.caution},' {adult.pronoun()} said, 'because {sdef.risk} is not a funny joke.'"
    )
    world.say(
        f"{params.name} nodded, then did the bravest careful thing of all: "
        f"{hero.pronoun().capitalize()} stepped back, pointed, and helped make a safer plan."
    )
    world.para()
    if params.swarm == "bees":
        ending = "They waited quietly until the bees buzzed up into a tree and left the path open again."
    elif params.swarm == "butterflies":
        ending = "They waved gently, and the butterflies fluttered away like tiny orange confetti."
    else:
        ending = "They let the ducklings follow their parent, and the splashing parade waddled away."
    world.say(
        f"{params.adult} laughed, because the plan was sensible and also a little silly. {ending}"
    )
    world.say(
        f"After that, {params.name} felt proud: {hero.pronoun().capitalize()} had been brave without being reckless, "
        f"and the day ended with a safe smile instead of a stingy surprise."
    )


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    sdef = SWARMS[p.swarm]
    return [
        f'Write a short comedy story for young children about bravery, caution, and "{p.swarm}".',
        f"Tell a gentle story where {p.name} sees {sdef.label} at {world.setting.place} and learns a careful brave choice.",
        f"Write a child-friendly story that includes {p.name}, {p.adult}, and the idea that being brave can still mean being cautious.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    sdef = SWARMS[p.swarm]
    return [
        QAItem(
            question=f"Who was the brave child in the story?",
            answer=f"The brave child was {p.name}, who explored {world.setting.place} and tried to stay calm."
        ),
        QAItem(
            question=f"What did {p.name} see near the path?",
            answer=f"{p.name} saw {sdef.label} near the path, making a noisy little scene."
        ),
        QAItem(
            question=f"How did {p.name} show bravery without being silly?",
            answer=f"{p.name} listened to {p.adult}, stepped back, and helped choose a safe plan instead of rushing closer."
        ),
        QAItem(
            question=f"Why did {p.adult} give a cautionary warning?",
            answer=f"{p.adult} warned {p.name} because {sdef.risk} could happen if the swarm was disturbed."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    sdef = SWARMS[p.swarm]
    return [
        QAItem(
            question="What is a swarm?",
            answer="A swarm is a large group moving together, often in a lively, buzzing, or fluttering bunch."
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking before acting so you can stay safe."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary even while you feel nervous."
        ),
        QAItem(
            question=f"What should people do when they see {sdef.label}?",
            answer=f"They should keep a safe distance and listen to a grown-up, just like {p.name} did."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, w) for s in SETTINGS for w in SWARMS]


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(setting="garden", swarm="bees", name="Mina", adult="Mom", trait="brave"),
    StoryParams(setting="playground", swarm="butterflies", name="Toby", adult="Dad", trait="curious"),
    StoryParams(setting="yard", swarm="ducklings", name="Nia", adult="Auntie", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible story combos")
        for s, w in sorted(valid_combos()):
            print(s, w)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.swarm} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
