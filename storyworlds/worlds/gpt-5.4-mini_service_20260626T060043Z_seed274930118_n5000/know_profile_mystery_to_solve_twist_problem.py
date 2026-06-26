#!/usr/bin/env python3
"""
storyworlds/worlds/know_profile_mystery_to_solve_twist_problem.py
===================================================================

A small space-adventure storyworld about a crew solving a mystery from a ship
profile, then discovering a twist in the problem and fixing it together.

The seed story premise:
---
A young space scout knows how to read star maps and ship profiles. One day the
crew's cargo drone stops working near a bright comet station. They think the
drone lost its route, but the real problem is stranger: the station's profile
file says the docking lights are on, while the station itself is dark. The scout
and the captain solve the mystery by checking the profile against the real sky.
The twist is that the drone was never lost; it was avoiding a hidden debris ring.
They adjust the route, clear the path, and the drone glides home safely.

This world supports a few close variations around:
- knowing / noticing a profile
- a mystery to solve
- a twist in what the problem really is
- problem solving in a space-adventure setting
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

METER_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "captain"}
        male = {"boy", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    sky: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    title: str
    clue: str
    twist: str
    problem: str
    fix: str
    danger: str
    tag: str
    keyword: str = "know"
    profile_word: str = "profile"


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    role: str
    captain: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "comet_station": Setting(
        place="Comet Station",
        sky="bright and busy",
        afford={"scan", "dock", "repair"},
    ),
    "asteroid_port": Setting(
        place="Asteroid Port",
        sky="dusty and starry",
        afford={"scan", "dock", "repair"},
    ),
    "moon_harbor": Setting(
        place="Moon Harbor",
        sky="silver and quiet",
        afford={"scan", "dock", "repair"},
    ),
}

MYSTERIES = {
    "dark_docks": Mystery(
        id="dark_docks",
        title="The Dark Docking Lights",
        clue="The station profile says the lights are on.",
        twist="The lights are broken, so the profile is stale.",
        problem="The drone keeps circling because it trusts the old profile.",
        fix="They update the route and use a flashlight beacon to guide the drone.",
        danger="a crash near the dock",
        tag="lights",
    ),
    "debris_ring": Mystery(
        id="debris_ring",
        title="The Hidden Debris Ring",
        clue="The profile looks normal, but the drone keeps turning away.",
        twist="A thin ring of spinning junk blocks the safest path.",
        problem="The drone thinks the route is clear, but the real sky is full of danger.",
        fix="They map the debris and steer around it carefully.",
        danger="scraped hull panels",
        tag="debris",
    ),
    "signal_echo": Mystery(
        id="signal_echo",
        title="The Echo in the Signal",
        clue="The profile repeats the same beacon twice.",
        twist="One beacon is only an echo bouncing off metal walls.",
        problem="The crew cannot tell which signal is real.",
        fix="They check the angle of the signal and choose the real beacon.",
        danger="a wrong turn into a dead end",
        tag="signal",
    ),
}

TRAITS = ["curious", "careful", "brave", "quick-thinking", "steady"]
NAMES = ["Mira", "Tari", "Niko", "Lina", "Pax", "Orin", "Sera", "Juno"]
ROLES = ["scout", "pilot", "mechanic", "navigator"]
CAPTAINS = ["captain", "commander"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def reasonableness_gate(setting: str, mystery: str) -> bool:
    return setting in SETTINGS and mystery in MYSTERIES


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M) :- setting(S), mystery(M).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure mystery solver storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--captain", choices=CAPTAINS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    captain = args.captain or rng.choice(CAPTAINS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, name=name, role=role, captain=captain, trait=trait)


def _narrate_intro(world: World, hero: Entity, captain: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a little {hero.traits[0]} {hero.type} who loved to know how things worked in space."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} kept a ship profile in {hero.pronoun('possessive')} pocket and read it like a treasure map."
    )
    world.say(
        f"On the ship, {captain.label} trusted {hero.id} to spot clues when the stars looked strange."
    )
    world.say(
        f"That day, the crew faced {mystery.title.lower()}. {mystery.clue}"
    )


def _solve_mystery(world: World, hero: Entity, captain: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} looked at the profile again and then at the real sky over {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} noticed something small: the profile and the sky did not match."
    )
    world.say(
        f"That was the mystery to solve, because the old profile could not explain the problem."
    )
    world.say(
        f"{captain.label} nodded and said it was time for careful problem solving."
    )


def _twist_and_fix(world: World, hero: Entity, captain: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(f"Then came the twist: {mystery.twist}")
    world.say(f"{mystery.problem}")
    world.say(
        f"{hero.id} knew what to do, and {captain.label} helped {hero.pronoun('object')} do it."
    )
    world.say(
        f"Together they used a clean route, a bright beacon, and steady hands to fix the trouble."
    )
    world.say(
        f"{mystery.fix} After that, the drone glided safely to the dock, and the crew could breathe again."
    )
    world.say(
        f"In the end, {hero.id} kept the profile, but now {hero.pronoun('subject')} knew to check the sky too."
    )


def tell(setting: Setting, mystery: Mystery, name: str, role: str, captain_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=role, traits=[trait, "space-sure"]))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_kind, label="the captain"))
    drone = world.add(Entity(id="Drone", kind="thing", type="drone", label="the cargo drone"))
    profile = world.add(Entity(id="Profile", kind="thing", type="profile", label="the ship profile"))

    world.facts.update(hero=hero, captain=captain, drone=drone, profile=profile, mystery=mystery, setting=setting)

    _narrate_intro(world, hero, captain, mystery)
    world.para()
    _solve_mystery(world, hero, captain, mystery)
    _twist_and_fix(world, hero, captain, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write a short space-adventure story for a young child that includes the word "know".',
        f"Tell a story where {hero.id} uses a ship profile to solve {mystery.title.lower()} and finds a twist.",
        f'Write a simple story about a mystery to solve, a twist, and problem solving in space, and include the word "profile".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who knew how to read the ship profile in the story?",
            answer=f"{hero.id} knew how to read the ship profile and spot the clue that helped solve the mystery.",
        ),
        QAItem(
            question=f"What problem did the crew have at {setting.place}?",
            answer=f"They had to solve {mystery.title.lower()}; the problem was that the profile did not match the real sky.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {mystery.twist.lower()}",
        ),
        QAItem(
            question=f"How did {hero.id} and {captain.label} fix things?",
            answer=f"They used careful problem solving, checked the real sky, and guided the drone along a safe route.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a profile?",
            answer="A profile is a description or record that gives useful information about something, like a ship route or a person.",
        ),
        QAItem(
            question="What does it mean to know something?",
            answer="To know something means to understand it well or remember it clearly.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something confusing or hidden that people try to figure out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="comet_station", mystery="dark_docks", name="Mira", role="scout", captain="captain", trait="curious"),
    StoryParams(setting="asteroid_port", mystery="debris_ring", name="Tari", role="navigator", captain="commander", trait="careful"),
    StoryParams(setting="moon_harbor", mystery="signal_echo", name="Niko", role="pilot", captain="captain", trait="brave"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.name, params.role, params.captain, params.trait)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible (setting, mystery) combos:\n")
        for s, m in combos:
            print(f"  {s:14} {m}")
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
            try:
                params = resolve_params(args, random.Random(seed))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
