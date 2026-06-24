#!/usr/bin/env python3
"""
A small nursery-rhyme story world about confusion with electronics, a mystery to
solve, and a misunderstanding that ends in a gentle fix.

Seed tale sketch:
---
Little Nell heard a buzz and found a tiny lamp that would not glow. She thought
the lamp was broken, but her brother said the batteries were missing. Nell looked
everywhere, discovered the batteries in a toy drum, and the light came back on.
They laughed, and the mystery was solved.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    functional: bool = True
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "sister", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "brother", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    requires: set[str] = field(default_factory=set)
    emits: str = "buzz"
    location: str = ""


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hides_in: set[str] = field(default_factory=set)
    found_in: str = ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero: str
    sibling: str
    device: str
    clue: str
    seed: Optional[int] = None


PLACES = {
    "nursery": Place(name="the nursery", indoors=True, affordances={"search", "play"}),
    "playroom": Place(name="the playroom", indoors=True, affordances={"search", "play"}),
    "kitchen": Place(name="the kitchen", indoors=True, affordances={"search"}),
    "porch": Place(name="the porch", indoors=False, affordances={"search"}),
}

HEROES = [
    ("Nell", "girl"),
    ("Milo", "boy"),
    ("Pip", "girl"),
    ("Finn", "boy"),
    ("Luna", "girl"),
]

SIBLINGS = [
    ("Sam", "boy"),
    ("Rose", "girl"),
    ("Tess", "girl"),
    ("Ben", "boy"),
]

DEVICES = {
    "lamp": Device(
        id="lamp",
        label="lamp",
        phrase="a small lamp with a round shade",
        requires={"battery"},
        emits="glow",
    ),
    "radio": Device(
        id="radio",
        label="radio",
        phrase="a tiny radio with a red button",
        requires={"battery"},
        emits="music",
    ),
    "nightlight": Device(
        id="nightlight",
        label="nightlight",
        phrase="a sleepy nightlight with a star on it",
        requires={"battery"},
        emits="glow",
    ),
}

CLUES = {
    "drawer": Clue(
        id="drawer",
        label="drawer",
        phrase="a blue drawer",
        hides_in={"battery"},
        found_in="drawer",
    ),
    "toy_drum": Clue(
        id="toy_drum",
        label="toy drum",
        phrase="a round toy drum",
        hides_in={"battery"},
        found_in="toy drum",
    ),
    "basket": Clue(
        id="basket",
        label="basket",
        phrase="a little basket by the bed",
        hides_in={"battery"},
        found_in="basket",
    ),
}

REASONS = {
    "battery_missing": "the batteries were missing",
    "batteries_hidden": "the batteries were tucked away in a toy",
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A device is in trouble when it needs a battery and no battery is present.
needs_battery(D) :- device(D), requires(D,battery).
missing_power(D) :- needs_battery(D), not has(battery).

% A clue can solve the mystery when it hides the missing battery.
solves(C, D) :- clue(C), missing_power(D), hides(C, battery).

% A good story has a place, a device, a missing-power mystery, and a clue.
valid_story(P, D, C) :- place(P), device(D), clue(C),
                        affords(P, search), solves(C, D).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affordances):
            lines.append(asp.fact("affords", pid, a))
    for did, d in DEVICES.items():
        lines.append(asp.fact("device", did))
        for req in sorted(d.requires):
            lines.append(asp.fact("requires", did, req))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for h in sorted(c.hides_in):
            lines.append(asp.fact("hides", cid, h))
    lines.append(asp.fact("has", "battery"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        if "search" not in place.affordances:
            continue
        for device_id, device in DEVICES.items():
            if "battery" not in device.requires:
                continue
            for clue_id, clue in CLUES.items():
                if "battery" in clue.hides_in:
                    combos.append((place_id, device_id, clue_id))
    return combos


def explain_rejection(place: str, device: str, clue: str) -> str:
    return (
        f"(No story: the chosen setup does not make a real mystery. "
        f"{DEVICES[device].label.capitalize()} needs a battery, and {CLUES[clue].label} "
        f"is not a convincing hiding place in {PLACES[place].name}.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def nursery_line(name: str, device: str) -> str:
    return {
        "lamp": f"{name} heard a buzz-buzz in the hush-hush night.",
        "radio": f"{name} heard a tippy-tap song in the quiet room.",
        "nightlight": f"{name} saw a sleepy little shimmer by the bed.",
    }[device]


def device_image(device: str) -> str:
    return {
        "lamp": "a small lamp with a round shade",
        "radio": "a tiny radio with a red button",
        "nightlight": "a sleepy nightlight with a star on it",
    }[device]


def clue_image(clue: str) -> str:
    return CLUES[clue].phrase


def generate_story(world: World, hero: Entity, sibling: Entity, device: Entity, clue: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved simple things and tidy strings of song."
    )
    world.say(
        f"One day {hero.id} found {device.phrase}. {hero.pronoun('subject').capitalize()} "
        f"wanted {device.label} to shine, hum, or sing."
    )
    world.para()
    world.say(nursery_line(hero.id, device.id))
    world.say(
        f"But the {device.label} would not work, for {REASONS['battery_missing']}."
    )
    world.say(
        f"{hero.id} frowned and thought, 'Oh dear, oh dear, what can it be?'"
    )
    sibling.memes["helpful"] += 1
    hero.memes["confusion"] += 1
    world.say(
        f"{sibling.id} peered near the bed and said, "
        f"'{device.label.capitalize()} is not broken, I think. We should solve the mystery.'"
    )
    world.para()
    world.say(
        f"They searched the {world.place.name} with careful feet. Under a book, behind a toy, "
        f"and in a little {clue.label}, they looked and looked."
    )
    clue.found_in = clue.label
    world.say(
        f"At last they found the missing battery in {clue.phrase}, just where no one first had thought to peek."
    )
    device.functional = True
    world.say(
        f"{hero.id} popped the battery back in, and at once {device.label} came to life with a happy {device.emits}."
    )
    hero.memes["confusion"] = 0.0
    hero.memes["joy"] += 1
    sibling.memes["joy"] += 1
    world.say(
        f"{hero.id} laughed a bright little laugh. The misunderstanding was gone, and the mystery was solved."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about confusion and electronics in {f["place_name"]}.',
        f"Tell a gentle mystery where {f['hero_name']} finds {device_image(f['device_id'])} "
        f"that does not work, then discovers why with help from {f['sibling_name']}.",
        f'Write a child-friendly story that includes a misunderstanding, a missing battery, and a happy fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    device = f["device"]
    clue = f["clue"]
    place = f["place"]
    return [
        QAItem(
            question=f"What was wrong with the {device.label} at first?",
            answer=f"It did not work because it needed a battery, and the battery was missing.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the mystery?",
            answer=f"{sibling.id} helped by searching carefully and noticing where the missing battery might be hiding.",
        ),
        QAItem(
            question=f"Where did they find the missing battery?",
            answer=f"They found it in {clue.phrase}, after looking all around {place.name}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the {device.label} started working again?",
            answer=f"{hero.id} felt happy and relieved, because the confusion was over and the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a battery for?",
            answer="A battery gives power to some toys and gadgets so they can light up, make sounds, or move.",
        ),
        QAItem(
            question="What does electronics mean?",
            answer="Electronics are things that use electricity to work, like lamps, radios, and other small gadgets.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks the wrong thing at first, but then learns the true answer.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to solve by looking for clues and thinking carefully.",
        ),
    ]


# ---------------------------------------------------------------------------
# Resolution / selection
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme story world about confusion, electronics, and a mystery to solve."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--sibling")
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--clue", choices=CLUES)
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
              if (args.place is None or c[0] == args.place)
              and (args.device is None or c[1] == args.device)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, device, clue = rng.choice(sorted(combos))
    hero_name, _hero_type = rng.choice(HEROES)
    sibling_name, _sib_type = rng.choice(SIBLINGS)
    return StoryParams(
        place=place,
        hero=args.hero or hero_name,
        sibling=args.sibling or sibling_name,
        device=device,
        clue=clue,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    world = World(place)
    hero_type = next(t for n, t in HEROES if n == params.hero) if params.hero else "girl"
    sibling_type = next(t for n, t in SIBLINGS if n == params.sibling) if params.sibling else "boy"

    hero = world.add(Entity(id=params.hero, kind="character", type=hero_type))
    sibling = world.add(Entity(id=params.sibling, kind="character", type=sibling_type))
    device_cfg = DEVICES[params.device]
    clue_cfg = CLUES[params.clue]
    device = world.add(Entity(
        id=device_cfg.id, kind="thing", type="device", label=device_cfg.label,
        phrase=device_cfg.phrase, functional=False, owner=hero.id, location=place.name,
    ))
    clue = world.add(Entity(
        id=clue_cfg.id, kind="thing", type="clue", label=clue_cfg.label,
        phrase=clue_cfg.phrase, location=place.name,
    ))

    world.facts.update(
        place=params.place,
        place_name=place.name,
        hero=hero,
        sibling=sibling,
        hero_name=hero.id,
        sibling_name=sibling.id,
        device=device,
        device_id=device.id,
        clue=clue,
    )

    generate_story(world, hero, sibling, device, clue)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
# Utilities
# ---------------------------------------------------------------------------
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
        if e.location:
            bits.append(f"location={e.location}")
        if e.functional is not None and e.kind == "thing":
            bits.append(f"functional={e.functional}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = ASP_RULES


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_show_program() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, device, clue) combos:\n")
        for c in combos:
            print(f"  {c[0]:9} {c[1]:10} {c[2]:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="nursery", hero="Nell", sibling="Sam", device="lamp", clue="toy_drum"),
            StoryParams(place="playroom", hero="Milo", sibling="Rose", device="radio", clue="drawer"),
            StoryParams(place="kitchen", hero="Pip", sibling="Ben", device="nightlight", clue="basket"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.hero}: {p.device} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
