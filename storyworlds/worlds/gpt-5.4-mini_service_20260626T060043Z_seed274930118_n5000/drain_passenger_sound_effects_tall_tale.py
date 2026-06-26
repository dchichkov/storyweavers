#!/usr/bin/env python3
"""
Tall-tale storyworld: a passenger, a drain, and the noisy adventure between them.

A child-facing, state-driven story engine with a tiny simulation, world QA,
and an ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    name: str
    flavor: str
    affords: set[str] = field(default_factory=set)


@dataclass
class PassengerRide:
    id: str
    label: str
    phrase: str
    motion: str
    sound: str
    risk: str
    turn_sound: str
    ending_sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    ride: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "street_drain": Setting(
        name="the street drain",
        flavor="A long grating drain yawned beside the road like a stone canyon.",
        affords={"gutter_skim", "rattle_run"},
    ),
    "old_culvert": Setting(
        name="the old culvert",
        flavor="The culvert curved under the hill like a giant hollow pipe.",
        affords={"gutter_skim", "whistle_wagon"},
    ),
    "harbor_drain": Setting(
        name="the harbor drain",
        flavor="The harbor drain sang whenever the tide pushed water through it.",
        affords={"whistle_wagon", "splash_skiff"},
    ),
}

RIDES = {
    "gutter_skim": PassengerRide(
        id="gutter_skim",
        label="a tin skiff",
        phrase="a little tin skiff",
        motion="skimming the water",
        sound="splish-splash",
        risk="the skiff might bob into the drain bars and scrape its nose",
        turn_sound="whish-whish",
        ending_sound="splish",
        tags={"drain", "passenger", "sound"},
    ),
    "rattle_run": PassengerRide(
        id="rattle_run",
        label="a cart with brass wheels",
        phrase="a cart with brass wheels",
        motion="rattling over the stones",
        sound="clack-clack",
        risk="the wheels might rattle so hard that the passenger would lose courage",
        turn_sound="clink-clink",
        ending_sound="clatter",
        tags={"drain", "passenger", "sound"},
    ),
    "whistle_wagon": PassengerRide(
        id="whistle_wagon",
        label="a wagon with a whistle horn",
        phrase="a wagon with a whistle horn",
        motion="rolling like a kingly parade",
        sound="woo-woo",
        risk="the whistle could echo so loudly that the drain would answer back",
        turn_sound="toot-toot",
        ending_sound="honk",
        tags={"drain", "passenger", "sound"},
    ),
    "splash_skiff": PassengerRide(
        id="splash_skiff",
        label="a snug skiff",
        phrase="a snug skiff with a bright seat",
        motion="floating through the dark water",
        sound="glug-glug",
        risk="the water might splash high enough to wet the passenger's scarf",
        turn_sound="glimmer-glug",
        ending_sound="glug",
        tags={"drain", "passenger", "sound"},
    ),
}

TRAITS = ["curious", "brave", "cheerful", "stubborn", "spry", "lively"]
GIRL_NAMES = ["Mina", "Ivy", "Nora", "Pia", "Lena"]
BOY_NAMES = ["Otis", "Finn", "Jude", "Theo", "Milo"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for ride_id in setting.affords:
            combos.append((setting_id, ride_id))
    return combos


def explain_rejection(setting: Setting, ride: PassengerRide) -> str:
    return (
        f"(No story: {ride.label} does not fit the way {setting.name} works. "
        f"Try a ride that belongs in that drain.)"
    )


def select_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def intro_line(hero: Entity, ride: PassengerRide, setting: Setting) -> str:
    return (
        f"{hero.id} was a {hero.memes.get('trait_word', 'curious')} passenger "
        f"who loved {ride.motion}. Folks said {setting.flavor}"
    )


def generate_story(world: World, hero: Entity, ride: PassengerRide) -> None:
    hero.memes["delight"] = 1
    hero.memes["wonder"] = 1
    world.say(
        f"{hero.id} was a {hero.memes['trait_word']} passenger who loved the noise of "
        f"{ride.sound} and the feeling of {ride.motion}."
    )
    world.say(
        f"On a wild day, {hero.id} climbed into {ride.phrase} and rode into {world.setting}."
    )
    world.say(
        f"Folks swore the place sounded like a giant fiddle case: {ride.sound}! {ride.sound}!"
    )

    world.para()
    hero.memes["worry"] = 1
    hero.meters["stuck"] = 1
    world.say(
        f"Then the drain began to croon a deep warning, and {ride.risk}."
    )
    world.say(
        f"{hero.id} held tight and listened, because every tall tale needs a brave ear."
    )

    world.para()
    hero.memes["courage"] = 1
    hero.meters["help"] = 1
    world.say(
        f"{hero.id} tapped the side of the ride and called, '{ride.turn_sound}! "
        f"Let's sing with the drain, not against it!'"
    )
    world.say(
        f"The sound bounced through the pipe, chased the stuck water, and made the jam loosen."
    )
    world.say(
        f"At last the drain answered with a cheerful {ride.ending_sound}, and the path opened wide."
    )
    world.say(
        f"{hero.id} sailed out smiling, with {ride.label} still shining and the drain "
        f"quiet as a sleeping bowl."
    )

    hero.meters["safe"] = 1
    hero.memes["pride"] = 1
    world.facts.update(hero=hero, ride=ride, setting=world.setting, resolved=True)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    ride = f["ride"]
    setting = f["setting"]
    return [
        f"Write a tall tale about a passenger named {hero.id} who rides through {setting} and hears {ride.sound}.",
        f"Tell a child-friendly story where a drain, a passenger, and a funny sound effect help solve a problem.",
        f"Compose a short tall tale about {hero.id}, {ride.label}, and the sound {ride.turn_sound}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ride = f["ride"]
    setting = f["setting"]
    trait = hero.memes["trait_word"]
    return [
        QAItem(
            question=f"Who was the passenger in the story?",
            answer=f"The passenger was {hero.id}, a {trait} child riding through {setting}.",
        ),
        QAItem(
            question=f"What sound kept showing up while {hero.id} rode?",
            answer=f"The noisy sound was {ride.sound}, and later the ride answered with {ride.turn_sound}.",
        ),
        QAItem(
            question=f"What helped the drain open again?",
            answer=f"{hero.id} listened, shouted {ride.turn_sound}, and the echo loosened the stuck water.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} came out smiling, and the drain was calm and open again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a drain?",
            answer="A drain is a channel that carries water away so streets and places do not stay flooded.",
        ),
        QAItem(
            question="What is a passenger?",
            answer="A passenger is someone who rides in a vehicle or boat instead of driving it.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a made-up or dramatic noise, like clang, whoosh, or splish, used to make a story feel lively.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S,R) :- setting(S), ride(R), affords(S,R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for r in sorted(s.affords):
            lines.append(asp.fact("affords", sid, r))
    for rid, r in RIDES.items():
        lines.append(asp.fact("ride", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with drains, passengers, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ride", choices=RIDES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.ride is None or c[1] == args.ride)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, ride_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or select_name(gender, rng)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting_id, ride=ride_id, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    ride = RIDES[params.ride]
    world = World(setting=setting.name)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={},
        memes={"trait_word": params.trait},
    ))
    generate_story(world, hero, ride)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes}")
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
    StoryParams(setting="street_drain", ride="gutter_skim", name="Mina", gender="girl", trait="curious"),
    StoryParams(setting="old_culvert", ride="whistle_wagon", name="Otis", gender="boy", trait="brave"),
    StoryParams(setting="harbor_drain", ride="splash_skiff", name="Nora", gender="girl", trait="lively"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, ride) combos:\n")
        for s, r in combos:
            print(f"  {s:13} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
