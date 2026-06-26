#!/usr/bin/env python3
"""
storyworlds/worlds/fiddle_kindness_curiosity_superhero_story.py
===============================================================

A small superhero-style story world about curiosity, kindness, and a fiddle.

Premise:
- A young hero with a curious heart notices a lonely problem in the city.
- A fiddle matters because music can gather a crowd, calm fear, or restore hope.

Turn:
- Curiosity leads the hero to investigate.
- The fiddle becomes important when someone needs help making a brave sound.

Resolution:
- Kindness turns the problem into a shared performance.
- The ending image proves the city changed: the music is back, and so is the courage.

This script is standalone and uses only stdlib plus the shared result containers.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    bearer: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class City:
    name: str
    place: str
    mood: str
    sound: str


@dataclass
class StoryParams:
    city: str
    hero_name: str
    hero_gender: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    fiddle_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.city)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

CITIES = {
    "sunspire": City(name="Sunspire", place="the bright city plaza", mood="bright", sound="busy bells"),
    "moonwharf": City(name="Moonwharf", place="the harbor walkway", mood="windy", sound="soft waves"),
    "pinegate": City(name="Pinegate", place="the roof garden", mood="green", sound="leafy rustles"),
}

HERO_NAMES = ["Nova", "Aster", "Mira", "Kite", "Juno", "Rio", "Tess", "Pax"]
SIDEKICK_NAMES = ["Milo", "Nia", "Toby", "Luna", "Zuri", "Owen"]
HERO_TYPES = ["girl", "boy"]
SIDEKICK_TYPES = ["bird", "cat", "robot", "fox"]

FIDDLE_STYLES = {
    "red_fiddle": ("a red fiddle", "fiddle", "the red fiddle"),
    "old_fiddle": ("an old fiddle", "fiddle", "the old fiddle"),
    "bright_fiddle": ("a bright fiddle", "fiddle", "the bright fiddle"),
}

TRAITS = ["curious", "kind", "brave", "gentle", "eager"]


# ---------------------------------------------------------------------------
# ASP twin: facts + rules
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Curiosity pushes the hero toward investigation.
wants_to_check(H) :- curious(H).

% Kindness makes help a natural goal.
wants_to_help(H) :- kind(H).

% A fiddle matters when someone needs music to feel brave.
needs_music(P) :- problem(P), about_music(P).

% A reasonable resolution exists if the hero can act with kindness and the
% fiddle can be used to help.
can_resolve(H, P) :- wants_to_help(H), needs_music(P), has_fiddle(H).

valid_story(City, Hero, Fiddle) :- city(City), hero(Hero), owned_fiddle(Hero, Fiddle).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, city in CITIES.items():
        lines.append(asp.fact("city", cid))
        lines.append(asp.fact("place", cid, city.place))
        lines.append(asp.fact("mood", cid, city.mood))
    for name in HERO_NAMES:
        lines.append(asp.fact("name", name))
    for name in SIDEKICK_NAMES:
        lines.append(asp.fact("sidekick_name", name))
    for fid in FIDDLE_STYLES:
        lines.append(asp.fact("fiddle", fid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style story world: kindness, curiosity, and a fiddle.")
    ap.add_argument("--city", choices=sorted(CITIES))
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
    city_key = args.city or rng.choice(list(CITIES))
    hero_name = rng.choice(HERO_NAMES)
    hero_gender = rng.choice(HERO_TYPES)
    hero_type = hero_gender
    sidekick_name = rng.choice(SIDEKICK_NAMES)
    sidekick_type = rng.choice(SIDEKICK_TYPES)
    fiddle_name = rng.choice(list(FIDDLE_STYLES))
    return StoryParams(
        city=city_key,
        hero_name=hero_name,
        hero_gender=hero_gender,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
        fiddle_name=fiddle_name,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.city not in CITIES:
        raise StoryError("The city must be one of the registered city choices.")
    if params.fiddle_name not in FIDDLE_STYLES:
        raise StoryError("The fiddle must be one of the registered fiddle choices.")


def _hero_label(hero: Entity) -> str:
    return hero.id


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    city = CITIES[params.city]
    world = World(city)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        meters={"hope": 0.0, "speed": 1.0},
        memes={"curiosity": 2.0, "kindness": 2.0, "heroism": 1.0},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick_name,
        kind="character",
        type=params.sidekick_type,
        meters={"worry": 1.0},
        memes={"shy": 1.0},
    ))
    fiddle_phrase, fiddle_type, fiddle_label = FIDDLE_STYLES[params.fiddle_name]
    fiddle = world.add(Entity(
        id=params.fiddle_name,
        kind="thing",
        type=fiddle_type,
        label="fiddle",
        phrase=fiddle_phrase,
        owner=hero.id,
        bearer=hero.id,
    ))

    world.facts.update(hero=hero, sidekick=sidekick, fiddle=fiddle, city=city)

    # Act 1: setup.
    world.say(f"In {city.name}, {hero.id} was a {params.hero_type} hero with a curious heart and a kind grin.")
    world.say(f"{hero.id} listened to the city's {city.sound} and noticed something unusual near {city.place}.")
    world.say(f"{hero.id} also carried {fiddle_phrase}, because music was one of the ways {hero.pronoun('subject')} helped people.")

    # Act 2: the problem.
    world.para()
    world.say(f"One afternoon, {sidekick.id} stood by the steps and looked worried.")
    world.say(f"{sidekick.id} wanted to play a tiny tune, but the strings on {fiddle_label} had gone quiet and slack.")
    world.say(f"{hero.id} felt curiosity spark. {hero.pronoun().capitalize()} leaned closer, then saw a loose peg hiding under a bench.")
    world.say(f"It was not a big disaster, but it was enough to stop the music and leave {sidekick.id} feeling small.")

    # Act 3: turn and resolution.
    world.para()
    world.say(f"{hero.id} chose kindness first. Instead of grabbing the fiddle away, {hero.pronoun()} asked, \"May I help?\"")
    world.say(f"{sidekick.id} nodded, and together they tightened the peg, smoothed the bow, and tried again.")
    world.say(f"At last, the fiddle sang out bright and clear across {city.place}.")
    world.say(f"{sidekick.id} smiled, less shy now, and {hero.id} stood beside {sidekick.id} like a tiny superhero who had saved the day with careful hands.")

    world.facts.update(
        problem="quiet_fiddle",
        resolution="music_restored",
        city_name=city.name,
        fiddle_name=fiddle_label,
    )

    prompts = [
        f"Write a superhero story for young children where a curious hero helps with a fiddle in {city.name}.",
        f"Tell a gentle adventure about {hero.id}, kindness, and a fiddle that needs help making music again.",
        f"Write a short story about a hero who uses curiosity to find a problem and kindness to fix it.",
    ]

    story_qa = [
        QAItem(
            question=f"Why did {hero.id} walk closer to the bench?",
            answer=f"{hero.id} was curious and noticed that something about the fiddle sounded wrong, so {hero.pronoun('subject')} went to look.",
        ),
        QAItem(
            question=f"How did {hero.id} help {sidekick.id}?",
            answer=f"{hero.id} helped by using kindness, asking to help first, and then fixing the loose peg on the fiddle with careful hands.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, the fiddle sang clearly again, {sidekick.id} smiled, and the city felt brighter because the music came back.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about what is happening.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help, speak gently, and care about how another person feels.",
        ),
        QAItem(
            question="What is a fiddle?",
            answer="A fiddle is a stringed musical instrument that can make lively songs and bright tunes.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model trace ---"]
    lines.append(f"city={world.city.name} place={world.city.place} mood={world.city.mood}")
    for ent in world.entities.values():
        parts = [f"type={ent.type}", f"kind={ent.kind}"]
        if ent.label:
            parts.append(f"label={ent.label}")
        if ent.phrase:
            parts.append(f"phrase={ent.phrase}")
        if ent.meters:
            parts.append(f"meters={ent.meters}")
        if ent.memes:
            parts.append(f"memes={ent.memes}")
        lines.append(f"{ent.id}: " + " ".join(parts))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------

def asp_valid_story_tuples() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # The world is tiny and deterministic; verify the ASP program grounds cleanly
    # and includes at least one candidate story.
    tuples = asp_valid_story_tuples()
    if not tuples:
        print("MISMATCH: ASP did not produce any valid_story/3 atoms.")
        return 1
    print(f"OK: ASP produced {len(tuples)} valid_story/3 atoms.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(city="sunspire", hero_name="Nova", hero_gender="girl", hero_type="girl", sidekick_name="Milo", sidekick_type="robot", fiddle_name="red_fiddle"),
    StoryParams(city="moonwharf", hero_name="Aster", hero_gender="boy", hero_type="boy", sidekick_name="Luna", sidekick_type="cat", fiddle_name="old_fiddle"),
    StoryParams(city="pinegate", hero_name="Mira", hero_gender="girl", hero_type="girl", sidekick_name="Zuri", sidekick_type="fox", fiddle_name="bright_fiddle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        tuples = asp_valid_story_tuples()
        print(f"{len(tuples)} valid story candidates:")
        for t in tuples:
            print(" ", t)
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} in {p.city} with {p.fiddle_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
