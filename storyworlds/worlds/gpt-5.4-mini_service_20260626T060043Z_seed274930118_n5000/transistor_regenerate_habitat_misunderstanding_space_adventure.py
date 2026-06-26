#!/usr/bin/env python3
"""
Storyworld: a small space-adventure misunderstanding about a habitat module.

Premise:
- A child crew member on a quiet ship needs to fix a habitat garden light.
- A tiny transistor inside the light stops working.
- The crew misunderstands "regenerate habitat" as a command to repair the whole
  habitat dome, not just the broken light.

The world is intentionally small and classical: one main problem, one mistaken
reaction, and one clean resolution.
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
    worn_by: Optional[str] = None
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "engineer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    name: str
    description: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    issue: str
    fix: str
    repair_action: str
    result_image: str


@dataclass
class StoryParams:
    place: str
    device: str
    name: str
    crew_role: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.location)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "ship_garden": Location(
        name="the ship garden deck",
        description="The ship garden deck glowed under a silver dome, with tiny vines climbing bright rails.",
        affords={"repair"},
    ),
    "orbital_habitat": Location(
        name="the orbital habitat ring",
        description="The habitat ring turned slowly above the stars, and every window looked out into black space.",
        affords={"repair"},
    ),
    "moon_bay": Location(
        name="the moon bay",
        description="The moon bay was quiet except for soft beeps and the hum of pumps.",
        affords={"repair"},
    ),
}

DEVICES = {
    "lamp": Device(
        id="lamp",
        label="garden lamp",
        phrase="a little garden lamp with a stubborn switch",
        issue="flickered and went dark",
        fix="transistor",
        repair_action="replace the transistor",
        result_image="shone warmly over the leaves again",
    ),
    "panel": Device(
        id="panel",
        label="greenhouse panel",
        phrase="a small greenhouse panel with a cracked controller",
        issue="blinked and stopped responding",
        fix="transistor",
        repair_action="swap the transistor",
        result_image="lit up the sprouts again",
    ),
    "beacon": Device(
        id="beacon",
        label="wayfinder beacon",
        phrase="a tiny wayfinder beacon with a loose board",
        issue="buzzed and went silent",
        fix="transistor",
        repair_action="replace the transistor",
        result_image="spun its blue light across the deck again",
    ),
}

HABITATS = {
    "garden": "habitat",
    "greenhouse": "habitat",
    "ring": "habitat",
}

CREW_NAMES = ["Mina", "Ravi", "Tess", "Niko", "Luna", "Orin", "Pia", "Juno"]
HELPERS = ["captain", "engineer", "bot"]
ROLES = ["cadet", "mechanic", "scout", "helper", "navigator"]

WORLD_KNOWLEDGE = {
    "transistor": (
        "What is a transistor?",
        "A transistor is a tiny electronic part that helps control how electricity flows in a device."
    ),
    "regenerate": (
        "What does regenerate mean?",
        "Regenerate means to grow back, repair, or make something work again."
    ),
    "habitat": (
        "What is a habitat?",
        "A habitat is the place where living things live, rest, and grow."
    ),
    "misunderstanding": (
        "What is a misunderstanding?",
        "A misunderstanding happens when someone hears a message the wrong way and thinks it means something else."
    ),
}

ASP_RULES = r"""
device_needs_fix(D) :- device(D).
clear_fix(D, transistor) :- device(D).
valid_story(P, D) :- place(P), device(D), clear_fix(D, transistor).
misunderstanding(P, D) :- place(P), device(D).
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.device not in DEVICES:
        raise StoryError("Unknown device.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.crew_role not in ROLES:
        raise StoryError("Unknown crew role.")


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    device = args.device or rng.choice(list(DEVICES))
    name = args.name or rng.choice(CREW_NAMES)
    crew_role = args.crew_role or rng.choice(ROLES)
    helper = args.helper or rng.choice(HELPERS)
    params = StoryParams(place=place, device=device, name=name, crew_role=crew_role, helper=helper)
    reasonableness_gate(params)
    return params


def _hero_label(hero: Entity) -> str:
    return hero.id


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _place_sentence(loc: Location) -> str:
    return loc.description


def _fix_sentence(device: Device, habitat_word: str) -> str:
    return (
        f"The broken {device.label} only needed a new transistor, not a whole new {habitat_word}."
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    loc = SETTINGS[params.place]
    device = DEVICES[params.device]
    habitat_word = HABITATS.get("garden" if "garden" in params.place else "ring", "habitat")

    world = World(loc)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Mina", "Tess", "Luna", "Pia", "Juno"} else "boy",
        label=params.crew_role,
        meters={"curiosity": 1.0},
        memes={"hope": 1.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="captain" if params.helper == "captain" else ("engineer" if params.helper == "engineer" else "bot"),
        label=params.helper,
        meters={"care": 1.0},
        memes={"calm": 1.0},
    ))
    gadget = world.add(Entity(
        id="Device",
        type="thing",
        label=device.label,
        phrase=device.phrase,
        owner=hero.id,
        caretaker=helper.id,
        meters={"broken": 1.0},
    ))

    # Act 1
    world.say(
        f"{_hero_label(hero)} was a young {params.crew_role} on a small ship, and {hero.pronoun('subject')} loved exploring the quiet corners of space."
    )
    world.say(
        f"One day, {hero.pronoun('subject')} found {gadget.phrase} in {loc.name}."
    )
    world.say(
        f"It had a tiny transistor inside, and when the part failed, the device {device.issue}."
    )

    # Act 2
    world.para()
    world.say(_place_sentence(loc))
    world.say(
        f"{hero.id} asked the helper to {device.repair_action}, but the message came out wrong."
    )
    world.say(
        f"The helper heard 'regenerate habitat' and thought the whole {habitat_word} needed fixing."
    )
    world.say(
        f"That was a misunderstanding, and soon space dust floated while big repair lights switched on."
    )
    world.say(
        f"{helper.label.capitalize()} hurried to check the walls, the vines, and the water lines instead of the little device."
    )

    # Act 3
    world.para()
    world.say(
        f"{hero.id} pointed to the open panel and said, '{_article(device.fix).capitalize()} {device.fix} is the part we need.'"
    )
    world.say(
        f"At last, the helper nodded and helped {hero.id} {device.repair_action}."
    )
    world.say(
        f"After the new transistor clicked into place, the {device.label} {device.result_image}."
    )
    world.say(
        f"The habitat stayed safe, and the small team laughed because the big fix had only needed a tiny part."
    )

    world.facts.update({
        "hero": hero,
        "helper": helper,
        "device": gadget,
        "device_cfg": device,
        "location": loc,
        "habitat_word": habitat_word,
        "misunderstanding": True,
        "resolved": True,
    })
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    device: Device = f["device_cfg"]  # type: ignore[assignment]
    loc: Location = f["location"]  # type: ignore[assignment]
    return [
        f"Write a short space adventure for a child named {hero.id} where a broken {device.label} in {loc.name} causes a misunderstanding.",
        f"Tell a gentle story in space that uses the words transistor, regenerate, and habitat, and ends with the team fixing only the small broken part.",
        f"Write a simple ship-deck story about a misunderstanding where someone thinks 'regenerate habitat' means a huge repair, but it really means fixing one tiny transistor.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    device: Device = f["device_cfg"]  # type: ignore[assignment]
    loc: Location = f["location"]  # type: ignore[assignment]
    habitat_word: str = f["habitat_word"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was broken in {loc.name}?",
            answer=f"A {device.label} was broken, and it only needed a tiny transistor to work again.",
        ),
        QAItem(
            question=f"Why did the helper start working on the whole {habitat_word}?",
            answer=f"The helper misunderstood the message and thought 'regenerate habitat' meant the entire habitat needed repair.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the problem?",
            answer=f"{hero.id} pointed to the open panel and explained that they only needed to replace the transistor.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The {device.label} shone again, the habitat stayed safe, and the crew could laugh about the misunderstanding.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    keys = ["transistor", "regenerate", "habitat", "misunderstanding"]
    return [QAItem(question=WORLD_KNOWLEDGE[k][0], answer=WORLD_KNOWLEDGE[k][1]) for k in keys]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for did in DEVICES:
        lines.append(asp.fact("device", did))
        lines.append(asp.fact("needs_part", did, "transistor"))
    lines.append(asp.fact("term", "transistor"))
    lines.append(asp.fact("concept", "regenerate"))
    lines.append(asp.fact("concept", "habitat"))
    lines.append(asp.fact("concept", "misunderstanding"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> set[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return set(asp.atoms(model, "valid_story"))


def python_valid() -> set[tuple[str, str]]:
    return {(p, d) for p in SETTINGS for d in DEVICES}


def asp_verify() -> int:
    left = asp_valid()
    right = python_valid()
    if left == right:
        print(f"OK: clingo gate matches Python ({len(left)} combinations).")
        return 0
    print("MISMATCH between clingo and Python:")
    if left - right:
        print("  only in clingo:", sorted(left - right))
    if right - left:
        print("  only in Python:", sorted(right - left))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with a misunderstanding about a habitat and a transistor.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--device", choices=list(DEVICES))
    ap.add_argument("--name")
    ap.add_argument("--crew-role", choices=ROLES)
    ap.add_argument("--helper", choices=HELPERS)
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
    return build_story_params(args, rng)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
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
    StoryParams(place="ship_garden", device="lamp", name="Mina", crew_role="cadet", helper="engineer"),
    StoryParams(place="orbital_habitat", device="panel", name="Ravi", crew_role="mechanic", helper="captain"),
    StoryParams(place="moon_bay", device="beacon", name="Tess", crew_role="scout", helper="bot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid combinations:")
        for p, d in combos:
            print(f"  {p} {d}")
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
