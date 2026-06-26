#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/petition_storage_straddle_cautionary_mystery_to_solve.py
===============================================================================================================

A small superhero storyworld about a cautionary mystery to solve.

Seed tale:
---
One afternoon, the city notice board was missing the petition that the mayor
had asked for. The petition had been stored in the hero's station drawer, but
the drawer was now open and empty. Mira, a young hero with a bright cape, saw
scuffed dust by the storage room and a bent latch on the cabinet. She noticed
that someone had straddled the hallway rope, leaving two muddy shoe prints
pointing in different directions.

Mira did not rush to guess. She followed the clues, checked the storage room,
and asked who had been there. At last she found that the paper had been moved
by accident when the sidekick used the wrong drawer. The petition was safe,
the storage cabinet was fixed, and Mira wrote a warning sign so nobody would
mix up the drawers again.

World model:
---
- Physical state includes where the petition is stored, whether cabinets are open,
  and whether clues are present.
- Emotional state includes caution, worry, and relief.
- The mystery begins when the petition goes missing from storage.
- The heroine solves it by tracing clues and correcting the storage mistake.
- The cautionary turn is a warning sign or rule that prevents the same mix-up.
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
# Entities and world
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    open: bool = False
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the city station"
    affords: set[str] = field(default_factory=lambda: {"petition", "storage", "straddle"})


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
SETTINGS = {
    "station": Setting(place="the city station"),
    "archive": Setting(place="the tower archive"),
    "garage": Setting(place="the hero garage"),
}

HEROES = [
    ("Mira", "girl"),
    ("Nova", "girl"),
    ("Jax", "boy"),
    ("Rio", "boy"),
]

SIDEKICKS = [
    ("Patch", "boy"),
    ("Bree", "girl"),
    ("Tuck", "boy"),
    ("Zee", "girl"),
]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def cautionary_mystery_reasonable(place: str) -> bool:
    return place in SETTINGS


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label="hero",
        meters={"courage": 1.0},
        memes={"caution": 1.0, "worry": 0.0, "relief": 0.0},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick_name,
        kind="character",
        type=params.sidekick_type,
        label="sidekick",
        meters={"helpfulness": 1.0},
        memes={"worry": 0.0},
    ))
    petition = world.add(Entity(
        id="petition",
        type="paper",
        label="petition",
        phrase="the important petition pages",
        owner=hero.id,
        location="storage cabinet",
        hidden=False,
    ))
    cabinet = world.add(Entity(
        id="cabinet",
        type="storage",
        label="storage cabinet",
        location=params.place,
        open=False,
        meters={"order": 1.0},
    ))
    sign = world.add(Entity(
        id="sign",
        type="thing",
        label="warning sign",
        phrase="a warning sign about the drawers",
        location="wall",
        hidden=True,
    ))
    rope = world.add(Entity(
        id="rope",
        type="thing",
        label="hallway rope",
        phrase="a hallway rope for keeping people back",
        location="hallway",
    ))

    world.facts.update(hero=hero, sidekick=sidekick, petition=petition, cabinet=cabinet, sign=sign, rope=rope)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.get(params.hero_name)
    sidekick = world.get(params.sidekick_name)
    petition = world.get("petition")
    cabinet = world.get("cabinet")
    sign = world.get("sign")
    rope = world.get("rope")

    # Setup
    world.say(
        f"{hero.id} was a little {hero.type} hero who protected {world.setting.place}."
    )
    world.say(
        f"{hero.id} and {sidekick.id} kept important papers in a storage cabinet so the city could find them fast."
    )
    world.para()

    # Mystery begins
    cabinet.open = True
    petition.hidden = True
    hero.memes["worry"] += 1
    world.say(
        f"One morning, {hero.id} opened the storage cabinet and found the petition missing."
    )
    world.say(
        f"The cabinet door was open, and a bent latch made the room feel strange."
    )
    world.say(
        f"By the hallway rope, there were two muddy prints where someone had straddled the rope in a hurry."
    )
    world.para()

    # Investigation
    world.say(
        f"{hero.id} did not guess right away. {hero.pronoun().capitalize()} checked the storage shelves, the floor, and the drawer labels."
    )
    world.say(
        f"{hero.id} asked {sidekick.id} who had last moved the papers."
    )
    sidekick.memes["worry"] += 1
    world.say(
        f"{sidekick.id} blinked and admitted that {sidekick.pronoun()} had used the wrong drawer by mistake."
    )
    world.say(
        f"The petition had not been stolen; it had been tucked into a different storage slot all along."
    )
    world.para()

    # Resolution and cautionary turn
    petition.hidden = False
    petition.location = "right drawer"
    cabinet.open = False
    sign.hidden = False
    hero.memes["relief"] += 1
    hero.memes["caution"] += 1
    world.say(
        f"{hero.id} moved the petition back into the right storage drawer and closed the cabinet carefully."
    )
    world.say(
        f"Then {hero.id} hung up a warning sign so nobody would mix up the drawers again."
    )
    world.say(
        f"At the end, the petition was safe, the cabinet was fixed, and the city board could read every line."
    )

    world.facts.update(
        petition_found=True,
        petition_hidden=False,
        cabinet_open=False,
        sign_visible=True,
        straddle_clue=True,
        mystery_solved=True,
        cautionary=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    return [
        f"Write a superhero story where {hero.id} investigates a missing petition in storage.",
        f"Tell a cautionary mystery about {hero.id} and {sidekick.id}, with a clue about someone who straddled a rope.",
        "Write a child-friendly superhero tale about a lost paper, a storage cabinet, and a warning that prevents the same mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    qa = [
        QAItem(
            question=f"What was missing from the storage cabinet?",
            answer="The petition was missing from the storage cabinet at first.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} notice that something strange had happened?",
            answer="The clue was the bent latch and the muddy prints where someone had straddled the hallway rope.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the mystery?",
            answer=f"{hero.id} checked the storage shelves, asked {sidekick.id} about the papers, and found that the petition had been put in the wrong drawer by mistake.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="The petition went back into the right drawer, the cabinet was closed, and a warning sign was put up so the same mix-up would not happen again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a petition?",
            answer="A petition is a paper where people write a request or ask for a change.",
        ),
        QAItem(
            question="What is storage?",
            answer="Storage is a place where you keep things safe and in order until you need them again.",
        ),
        QAItem(
            question="What does it mean to straddle something?",
            answer="To straddle something means to stand or sit with one leg on each side of it.",
        ),
        QAItem(
            question="Why do people use warning signs?",
            answer="People use warning signs to help others stay safe and avoid the same mistake.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.open:
            bits.append("open=True")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A petition story is valid when the place supports the core domain elements.
valid_place(P) :- place(P).

% The petition is in storage, the storage is opened, and the clue exists.
missing_petition :- petition_missing.
straddle_clue :- clue_straddle.

% The cautionary ending requires that a warning sign is installed.
cautionary :- warning_installed.

% The storyworld answer set should include the supported story location.
story_ok(P) :- valid_place(P), petition_story(P), mystery(P), cautionary.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import inside ASP helpers
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("petition_story", pid))
        lines.append(asp.fact("mystery", pid))
    lines.append(asp.fact("petition_missing"))
    lines.append(asp.fact("clue_straddle"))
    lines.append(asp.fact("warning_installed"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import inside ASP helpers
    model = asp.one_model(asp_program("#show story_ok/1."))
    asp_places = sorted(set(asp.atoms(model, "story_ok")))
    py_places = sorted((p,) for p in SETTINGS)
    if asp_places == py_places:
        print(f"OK: clingo gate matches Python gate ({len(py_places)} places).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", asp_places)
    print("  python:", py_places)
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero cautionary mystery storyworld about petition, storage, and straddle.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-type", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(SETTINGS))
    if not cautionary_mystery_reasonable(place):
        raise StoryError("The chosen place does not support this cautionary mystery.")
    hero_name, hero_type = (args.hero_name, args.hero_type) if args.hero_name and args.hero_type else rng.choice(HEROES)
    sidekick_name, sidekick_type = (args.sidekick_name, args.sidekick_type) if args.sidekick_name and args.sidekick_type else rng.choice(SIDEKICKS)
    if hero_name == sidekick_name:
        raise StoryError("The hero and sidekick must be different characters.")
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="station", hero_name="Mira", hero_type="girl", sidekick_name="Patch", sidekick_type="boy"),
    StoryParams(place="archive", hero_name="Nova", hero_type="girl", sidekick_name="Bree", sidekick_type="girl"),
    StoryParams(place="garage", hero_name="Jax", hero_type="boy", sidekick_name="Tuck", sidekick_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show story_ok/1."))
        print(sorted(set(asp.atoms(model, "story_ok"))))
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
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
