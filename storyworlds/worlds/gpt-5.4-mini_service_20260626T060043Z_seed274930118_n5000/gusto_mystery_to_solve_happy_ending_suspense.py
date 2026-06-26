#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gusto_mystery_to_solve_happy_ending_suspense.py
=================================================================================================

A small superhero story world about a mystery to solve with gusto, suspense,
and a happy ending.

Premise seed:
---
A young hero loved helping people with gusto. One evening, something mysterious
kept going missing in the city. The hero followed clues through a little bit of
suspense, found the cause, and ended the night with everyone safe and smiling.

World idea:
- A hero has a small set of abilities and a favorite gadget.
- A mystery item disappears from a city location.
- A clue trail builds suspense.
- The hero investigates, reasons through the mismatch, and resolves the case.
- The ending proves the change by restoring the missing item and calming fear.

This file is self-contained and follows the Storyweavers contract.
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
# Shared vocabulary
# ---------------------------------------------------------------------------
CITY_PLACES = {
    "library": "the library",
    "museum": "the museum",
    "bakery": "the bakery",
    "park": "the park",
    "dock": "the dock",
    "tower": "the clock tower",
}

DAY_TIMES = ["morning", "afternoon", "evening", "night"]

EMOTIONS = ["calm", "curious", "brave", "hopeful", "worried", "proud"]

HERO_NAMES = ["Nova", "Jet", "Milo", "Ruby", "Sky", "Piper", "Bram", "Iris"]
SIDEKICK_NAMES = ["Pip", "Dot", "Sparky", "Munch", "Wisp"]

POWERS = {
    "speed": "speed",
    "light": "light",
    "listening": "super listening",
    "stretch": "stretching",
    "glow": "glowing hands",
}

GADGETS = {
    "scanner": "a clue scanner",
    "gloves": "grippy gloves",
    "lamp": "a bright lamp",
    "rope": "a little rescue rope",
    "mask": "a wind mask",
}

MYSTERIES = {
    "missing_map": {
        "item": "map",
        "item_phrase": "the museum map",
        "place": "museum",
        "suspects": ["curator", "delivery cart", "wind"],
        "truth": "the map had blown behind a display case",
        "clue": "a paper corner sticking out near the wall",
        "wrong_guess": "a sneaky thief",
    },
    "missing_cakes": {
        "item": "cakes",
        "item_phrase": "the bakery cakes",
        "place": "bakery",
        "suspects": ["cat", "open window", "sleepy helper"],
        "truth": "the cakes had been moved to the cooling shelf",
        "clue": "crumbs leading to the back counter",
        "wrong_guess": "a hungry robber",
    },
    "missing_balloon": {
        "item": "balloons",
        "item_phrase": "the park balloons",
        "place": "park",
        "suspects": ["wind", "kite string", "a laughing child"],
        "truth": "the balloons had floated into a tree and were waiting there",
        "clue": "a string caught on a branch",
        "wrong_guess": "a balloon bandit",
    },
    "missing_key": {
        "item": "key",
        "item_phrase": "the dock key",
        "place": "dock",
        "suspects": ["seagull", "crate", "splashing wave"],
        "truth": "the key had slipped under a crate",
        "clue": "a tiny glint under wood",
        "wrong_guess": "a masked villain",
    },
}

REGISTRY_ORDER = ["speed", "light", "listening", "stretch", "glow"]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    sidekick: str
    power: str
    gadget: str
    mood: str = "gusto"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: str
    time: str
    mystery: str
    hero: Entity = field(default=None)
    sidekick: Entity = field(default=None)
    item: Entity = field(default=None)
    suspects: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        w = World(self.place, self.time, self.mystery)
        w.hero = copy.deepcopy(self.hero)
        w.sidekick = copy.deepcopy(self.sidekick)
        w.item = copy.deepcopy(self.item)
        w.suspects = list(self.suspects)
        w.facts = dict(self.facts)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------
def introduce(world: World) -> None:
    hero = world.hero
    sidekick = world.sidekick
    world.say(
        f"{hero.id} was a little superhero with {world.facts['power_phrase']} and a big heart."
    )
    world.say(
        f"{hero.id} always helped with gusto, and {sidekick.id} loved racing along for the fun."
    )


def setup_mystery(world: World) -> None:
    hero = world.hero
    item = world.item
    world.say(
        f"One {world.time}, {item.phrase} went missing from {world.place}."
    )
    world.say(
        f"People whispered about {world.facts['wrong_guess']}, and the city grew quiet with suspense."
    )
    hero.memes["curiosity"] = 1.0
    hero.memes["gusto"] = 1.0


def investigate(world: World) -> None:
    hero = world.hero
    sidekick = world.sidekick
    clue = world.facts["clue"]
    world.para()
    world.say(
        f"{hero.id} arrived with {sidekick.id}, looked carefully around, and listened for clues."
    )
    world.say(
        f"Using {world.facts['gadget_phrase']}, {hero.id} followed {clue}."
    )
    world.say(
        f"That made the suspense grow, because the clue was small but it pointed somewhere real."
    )
    hero.memes["focus"] = 1.0


def test_guess(world: World) -> None:
    world.say(
        f"At first, {world.hero.id} thought it might be {world.facts['wrong_guess']}."
    )
    world.say(
        f"But the clue did not fit that guess, so {world.hero.id} kept going instead of giving up."
    )


def resolve(world: World) -> None:
    hero = world.hero
    item = world.item
    truth = world.facts["truth"]
    world.para()
    world.say(
        f"Then {hero.id} noticed the last clue and smiled."
    )
    world.say(
        f"The answer was {truth}."
    )
    item.hidden = False
    item.carried_by = None
    hero.memes["relief"] = 1.0
    hero.memes["pride"] = 1.0
    world.say(
        f"{hero.id} brought back {item.phrase}, and the worried people cheered."
    )
    world.say(
        f"The city felt bright again, and {hero.id} went home with {world.facts['sidekick_name']} laughing beside {hero.pronoun('object')}."
    )


def tell(params: StoryParams) -> World:
    myst = MYSTERIES[params.mystery]
    world = World(place=CITY_PLACES[params.place], time=random.choice(DAY_TIMES), mystery=params.mystery)

    hero_type = "girl" if params.name in {"Ruby", "Iris", "Nova", "Sky", "Piper"} else "boy"
    hero = world.add(Entity(id=params.name, kind="character", type=hero_type))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="thing"))
    item = world.add(Entity(
        id=myst["item"],
        kind="thing",
        type="thing",
        label=myst["item"],
        phrase=myst["item_phrase"],
        hidden=True,
        owner=world.place,
    ))
    world.hero = hero
    world.sidekick = sidekick
    world.item = item
    world.suspects = list(myst["suspects"])

    world.facts.update(
        power=params.power,
        power_phrase=POWERS[params.power],
        gadget=params.gadget,
        gadget_phrase=GADGETS[params.gadget],
        wrong_guess=myst["wrong_guess"],
        clue=myst["clue"],
        truth=myst["truth"],
        sidekick_name=params.sidekick,
        mystery_item=myst["item"],
        place=params.place,
        place_name=world.place,
        mood=params.mood,
    )

    introduce(world)
    setup_mystery(world)
    investigate(world)
    test_guess(world)
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
def valid_combo(place: str, mystery: str, power: str, gadget: str) -> bool:
    m = MYSTERIES[mystery]
    if place != m["place"]:
        return False
    if power == "listening" and gadget == "mask":
        return True
    if power == "light" and gadget in {"lamp", "scanner"}:
        return True
    if power == "speed" and gadget in {"rope", "gloves"}:
        return True
    if power == "stretch" and gadget in {"rope", "gloves"}:
        return True
    if power == "glow" and gadget in {"lamp", "scanner"}:
        return True
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in CITY_PLACES:
        for mystery in MYSTERIES:
            for power in POWERS:
                for gadget in GADGETS:
                    if valid_combo(place, mystery, power, gadget):
                        out.append((place, mystery, power, gadget))
    return out


@dataclass
class StoryParamsRegistry:
    names: list[str] = field(default_factory=lambda: HERO_NAMES)
    sidekicks: list[str] = field(default_factory=lambda: SIDEKICK_NAMES)
    powers: list[str] = field(default_factory=lambda: list(POWERS))
    gadgets: list[str] = field(default_factory=lambda: list(GADGETS))


PARAMS_REGISTRY = StoryParamsRegistry()


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a small child that includes the word "gusto" and a mystery to solve.',
        f"Tell a suspenseful but happy story about {world.hero.id} using {f['power_phrase']} and {f['gadget_phrase']} to solve a missing-{f['mystery_item']} case.",
        f"Write a gentle superhero mystery set at {world.place} where a brave hero follows clues and ends with a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.hero
    sidekick = world.sidekick
    item = world.item
    return [
        QAItem(
            question=f"Who solved the mystery at {world.place}?",
            answer=f"{hero.id} solved the mystery with help from {sidekick.id}.",
        ),
        QAItem(
            question=f"What went missing in the story?",
            answer=f"{item.phrase} went missing.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the case?",
            answer=(
                f"{hero.id} used {f['power_phrase']} and {f['gadget_phrase']} to follow the clues, "
                f"then found that {f['truth']}."
            ),
        ),
        QAItem(
            question=f"Why was there suspense in the story?",
            answer=(
                f"There was suspense because people thought {f['wrong_guess']}, but the real answer was not known yet."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended happily when {hero.id} brought back {item.phrase} and the city cheered."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzling problem where people do not know the answer at first.",
        ),
        QAItem(
            question="What does gusto mean?",
            answer="Gusto means doing something with lively energy and happy enthusiasm.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next.",
        ),
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave helper who uses special powers or tools to protect others.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story combo is valid when the place matches the mystery and the hero's
% power/gadget pairing can plausibly help solve it.
helpful(speed, rope).
helpful(speed, gloves).
helpful(stretch, rope).
helpful(stretch, gloves).
helpful(light, lamp).
helpful(light, scanner).
helpful(glow, lamp).
helpful(glow, scanner).
helpful(listening, mask).

valid(Place, Mystery, Power, Gadget) :-
    story_place(Mystery, Place),
    helpful(Power, Gadget).

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place_name in CITY_PLACES.items():
        lines.append(asp.fact("city_place", place_id))
    for mid, spec in MYSTERIES.items():
        lines.append(asp.fact("story_place", mid, spec["place"]))
    for power in POWERS:
        lines.append(asp.fact("power", power))
    for gadget in GADGETS:
        lines.append(asp.fact("gadget", gadget))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP and Python agree on {len(py)} valid combos.")
        return 0
    print("MISMATCH between ASP and Python valid-combo gates.")
    if py - asp_set:
        print("Python only:", sorted(py - asp_set))
    if asp_set - py:
        print("ASP only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero mystery story world with gusto, suspense, and a happy ending.")
    ap.add_argument("--place", choices=CITY_PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--gadget", choices=GADGETS)
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.power is None or c[2] == args.power)
        and (args.gadget is None or c[3] == args.gadget)
    ]
    if not filtered:
        raise StoryError("No valid superhero mystery matches the requested options.")
    place, mystery, power, gadget = rng.choice(filtered)
    name = args.name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    return StoryParams(place=place, mystery=mystery, name=name, sidekick=sidekick, power=power, gadget=gadget, seed=args.seed)


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
        print("--- trace ---")
        print(json.dumps(sample.world.facts, indent=2, ensure_ascii=False))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="museum", mystery="missing_map", name="Nova", sidekick="Pip", power="light", gadget="scanner"),
    StoryParams(place="bakery", mystery="missing_cakes", name="Ruby", sidekick="Dot", power="speed", gadget="gloves"),
    StoryParams(place="park", mystery="missing_balloon", name="Jet", sidekick="Sparky", power="stretch", gadget="rope"),
    StoryParams(place="dock", mystery="missing_key", name="Iris", sidekick="Wisp", power="listening", gadget="mask"),
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
        model = asp.one_model(asp_program())
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid combos")
        for c in combos:
            print(c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} / {p.mystery} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
