#!/usr/bin/env python3
"""
storyworlds/worlds/glee_corduroy_spastic_twist_flashback_mystery_to.py
======================================================================

A standalone story world for a tiny superhero-style mystery with a twist and a
flashback.

Premise:
- A child hero in corduroy clothes wants to solve a puzzling problem in a small
  city setting.
- A spastic little gadget, an old clue, and a flashback reveal that the
  mystery is not a villain at all, but a misplaced helper and a mistaken
  accusation.
- The story ends with glee when the hero uses the right method and restores
  trust.

This world keeps the prose concrete and state-driven:
- physical meters: distance, mess, signal, damage, brightness
- emotional memes: glee, worry, trust, surprise, relief, suspicion

It includes:
- Twist
- Flashback
- Mystery to Solve
- Superhero Story style

The script supports:
- default run, -n, --all, --seed, --trace, --qa, --json
- --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    carries: str = ""
    worn: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    culprit: str
    method: str
    flashback: str
    twist: str
    resolves_with: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HeroGear:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    gear: str
    name: str
    hero_type: str
    sidekick: str
    sidekick_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "rooftop": Setting(
        place="the rooftop",
        detail="The rooftop was bright with little antenna shadows and warm city wind.",
        affords={"search", "signal"},
    ),
    "alley": Setting(
        place="the alley",
        detail="The alley sat between tall buildings, with wet bricks and echoing pipes.",
        affords={"search", "signal"},
    ),
    "museum": Setting(
        place="the museum hall",
        detail="The museum hall was quiet, full of glass cases and echoing footsteps.",
        affords={"search", "flashback"},
    ),
}

MYSTERIES = {
    "missing_mascot": Mystery(
        id="missing_mascot",
        clue="a tiny red badge with a star on it",
        culprit="the wind",
        method="slipped under a bench and rolled into a drain",
        flashback="the hero remembered seeing a flutter of red near the storm grate",
        twist="the missing mascot was not stolen at all",
        resolves_with="carefully checking the drain cover and following the clue",
        tags={"mystery", "flashback", "twist", "glee"},
    ),
    "wrong_villain": Mystery(
        id="wrong_villain",
        clue="a torn cape stuck on a fence nail",
        culprit="a sleepy rescue drone",
        method="caught on a corner and left a trail of silver thread",
        flashback="the hero flashed back to the drone wobbling by the window",
        twist="the blamed villain was only trying to help",
        resolves_with="spotting the silver thread and asking the drone what happened",
        tags={"mystery", "flashback", "twist"},
    ),
    "lost_lunchbox": Mystery(
        id="lost_lunchbox",
        clue="a blue lunchbox with a lightning sticker",
        culprit="the school bus",
        method="bumped loose during a bouncy turn at the curb",
        flashback="the hero remembered the bus jostling over a crack in the road",
        twist="the lunchbox had never left the neighborhood",
        resolves_with="replaying the route and tracing the bump marks",
        tags={"mystery", "flashback", "twist"},
    ),
}

GEAR = {
    "corduroy_suit": HeroGear(
        id="corduroy_suit",
        label="corduroy suit",
        phrase="a neat corduroy suit",
        helps={"search"},
        covers={"knees", "elbows"},
        tags={"corduroy"},
    ),
    "spastic_brace": HeroGear(
        id="spastic_brace",
        label="spastic brace",
        phrase="a springy spastic brace",
        helps={"signal"},
        covers={"wrist"},
        tags={"spastic"},
    ),
    "signal_glove": HeroGear(
        id="signal_glove",
        label="signal glove",
        phrase="a bright signal glove",
        helps={"signal", "search"},
        covers={"hand"},
        tags={"signal"},
    ),
}

NAMES = ["Ava", "Milo", "Zoe", "Leo", "Nina", "Finn", "Iris", "Owen"]
SIDEKICKS = ["Pip", "Juno", "Rex", "Tally", "Dot", "Bix"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for g in GEAR:
                combos.append((s, m, g))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero mystery story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--hero-type", choices=["girl", "boy"], dest="hero_type")
    ap.add_argument("--sidekick-type", choices=["girl", "boy"], dest="sidekick_type")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, gear = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    sidekick_type = args.sidekick_type or ("boy" if hero_type == "girl" else "girl")
    name = args.name or rng.choice([n for n in NAMES if n != (args.sidekick or "")])
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(setting=setting, mystery=mystery, gear=gear, name=name,
                       hero_type=hero_type, sidekick=sidekick,
                       sidekick_type=sidekick_type)


def scene_intro(world: World, hero: Entity, sidekick: Entity, mystery: Mystery, gear: HeroGear) -> None:
    hero.memes["glee"] += 1
    sidekick.memes["glee"] += 1
    world.say(
        f"{hero.id} wore {gear.phrase} and felt ready for anything. "
        f"{sidekick.id} hurried beside {hero.pronoun('object')} like a tiny sidekick."
    )
    world.say(
        f"They had a mystery to solve: {mystery.clue} had gone missing from {world.setting.place}."
    )


def flashback(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["surprise"] += 1
    world.say(
        f"Then came a flashback. {mystery.flashback}. "
        f"That old picture in {hero.pronoun('possessive')} mind felt important."
    )


def twist(world: World, mystery: Mystery) -> None:
    world.say(
        f"The twist was simple and strange: {mystery.twist}. "
        f"The wrong story everyone guessed was not the true one."
    )


def solve(world: World, hero: Entity, sidekick: Entity, mystery: Mystery, gear: HeroGear) -> None:
    hero.memes["trust"] += 1
    sidekick.memes["trust"] += 1
    hero.meters["distance"] += 1
    world.say(
        f"{hero.id} used {gear.label} to {mystery.resolves_with}, and {sidekick.id} pointed at the clue."
    )
    world.say(
        f"At last they found the answer: {mystery.culprit} had caused the trouble {mystery.method}."
    )
    hero.memes["glee"] += 2
    sidekick.memes["glee"] += 2
    hero.memes["relief"] += 1
    sidekick.memes["relief"] += 1
    world.say(
        f"{hero.id} grinned with glee, because the mystery was solved and the city felt safe again."
    )


def tell(setting: Setting, mystery: Mystery, gear: HeroGear,
         name: str = "Ava", hero_type: str = "girl",
         sidekick: str = "Pip", sidekick_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id=sidekick, kind="character", type=sidekick_type, role="sidekick"))
    item = world.add(Entity(id="clue", type="thing", label="clue"))
    world.facts.update(hero=hero, sidekick=helper, mystery=mystery, gear=gear, clue=item)
    scene_intro(world, hero, helper, mystery, gear)
    world.para()
    flashback(world, hero, mystery)
    world.para()
    twist(world, mystery)
    world.para()
    solve(world, hero, helper, mystery, gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a Superhero Story for a young child where {f["hero"].id} in {world.setting.place} has a mystery to solve, a flashback, and a twist.',
        f"Tell a gentle mystery story where {f['hero'].id} uses {f['gear'].label} to solve a clue about {f['mystery'].clue}.",
        f'Write a story with glee, corduroy, and spastic details, ending with the mystery solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    gear = f["gear"]
    sidekick = f["sidekick"]
    return [
        QAItem(
            question=f"What was {hero.id}'s mystery to solve?",
            answer=f"{hero.id} had to solve a mystery about {mystery.clue} at {world.setting.place}.",
        ),
        QAItem(
            question="What was the flashback for?",
            answer=f"It helped {hero.id} remember {mystery.flashback.lower()}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {mystery.twist}.",
        ),
        QAItem(
            question=f"How did {hero.id} solve it?",
            answer=f"{hero.id} used {gear.label} and worked with {sidekick.id} to follow the clue.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does glee mean?",
            answer="Glee is a big happy feeling, like being so glad you want to smile and jump.",
        ),
        QAItem(
            question="What is corduroy?",
            answer="Corduroy is a cloth with soft ridges in it, often used for pants or jackets.",
        ),
        QAItem(
            question="What does spastic mean here?",
            answer="Here it means quick, springy, and a little bouncy in movement.",
        ),
    ]
    return out


ASP_RULES = r"""
hero(X) :- chosen_hero(X).
mystery(M) :- chosen_mystery(M).
gear(G) :- chosen_gear(G).
solved :- flashback_seen, twist_seen, clue_followed.
flashback_seen :- story_feature(flashback).
twist_seen :- story_feature(twist).
clue_followed :- story_feature(mystery_to_solve).
valid_story(S, M, G) :- setting(S), mystery(M), gear(G), solved.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_def", m))
    for g in GEAR:
        lines.append(asp.fact("gear_def", g))
    for feat in ["flashback", "twist", "mystery_to_solve"]:
        lines.append(asp.fact("story_feature", feat))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        GEAR[params.gear],
        params.name,
        params.hero_type,
        params.sidekick,
        params.sidekick_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={dict(m)}")
        if n:
            bits.append(f"memes={dict(n)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    StoryParams(setting="rooftop", mystery="missing_mascot", gear="corduroy_suit",
                name="Ava", hero_type="girl", sidekick="Pip", sidekick_type="boy"),
    StoryParams(setting="alley", mystery="wrong_villain", gear="signal_glove",
                name="Milo", hero_type="boy", sidekick="Juno", sidekick_type="girl"),
    StoryParams(setting="museum", mystery="lost_lunchbox", gear="spastic_brace",
                name="Iris", hero_type="girl", sidekick="Rex", sidekick_type="boy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, gear = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        mystery=mystery,
        gear=gear,
        name=args.name or rng.choice(NAMES),
        hero_type=args.hero_type or rng.choice(["girl", "boy"]),
        sidekick=args.sidekick or rng.choice(SIDEKICKS),
        sidekick_type=args.sidekick_type or rng.choice(["girl", "boy"]),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
