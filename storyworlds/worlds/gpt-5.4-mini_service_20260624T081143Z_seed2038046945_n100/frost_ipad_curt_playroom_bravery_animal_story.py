#!/usr/bin/env python3
"""
storyworlds/worlds/frost_ipad_curt_playroom_bravery_animal_story.py
===================================================================

A small standalone storyworld built from the seed words:
frost, ipad, curt

Premise:
- In a playroom, a child named Curt wants to use an iPad.
- The iPad is frozen up by frost from a chilly toy-room accident.
- Curt is tempted to poke at it, but bravery means asking for help and doing
  the careful fix instead of rushing in.

This world keeps the "Animal Story" feel: a simple child, a small problem,
a worried moment, a brave choice, and a gentle ending image showing what
changed. The physical state and emotional state both matter:
- physical meters: cold, icy, wiped, powered
- emotional memes: worry, bravery, pride, patience

The story generator is deterministic from StoryParams, supports the standard
CLI, and includes an inline ASP twin for reasonableness checks.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    touched_by: Optional[str] = None
    used_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"cold": 0.0, "icy": 0.0, "wiped": 0.0, "powered": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "bravery": 0.0, "pride": 0.0, "patience": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the playroom"
    affords: set[str] = field(default_factory=lambda: {"ipad"})


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    fix: str
    warm_step: str
    final_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    device: str
    name: str = "Curt"
    gender: str = "boy"
    helper: str = "mom"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "playroom": Setting(place="the playroom", affords={"ipad"}),
}

DEVICES = {
    "ipad": Device(
        id="ipad",
        label="iPad",
        phrase="a shiny iPad",
        fix="wipe the frost away with a soft cloth",
        warm_step="set it near the warm lamp for a little while",
        final_image="the screen glowed bright and clear",
        tags={"frost", "ipad"},
    ),
}

HELPERS = {
    "mom": "mom",
    "dad": "dad",
    "grandma": "grandma",
}

NAMES = ["Curt", "Milo", "Nia", "Theo", "Pia"]
GENDERS = ["boy", "girl"]


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
device(D) :- device_id(D).
good_story(P, D) :- in_place(P), device(D), afford(P, D).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for did, dev in DEVICES.items():
        lines.append(asp.fact("device_id", did))
        for tag in sorted(dev.tags):
            lines.append(asp.fact("tag", did, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show good_story/2."))
    asp_pairs = sorted(set(asp.atoms(model, "good_story")))
    py_pairs = sorted(valid_combos())
    if asp_pairs == py_pairs:
        print(f"OK: clingo gate matches Python gate ({len(py_pairs)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("ASP:", asp_pairs)
    print("PY :", py_pairs)
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for place in SETTINGS:
        for dev in DEVICES:
            out.append((place, dev))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny playroom storyworld about Curt, frost, and a brave iPad fix."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--device", choices=DEVICES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPERS.keys())
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
    place = args.place or rng.choice(list(SETTINGS))
    device = args.device or rng.choice(list(DEVICES))
    if (place, device) not in valid_combos():
        raise StoryError("That place and device do not make a reasonable story here.")
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or ("Curt" if gender == "boy" else rng.choice(NAMES))
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, device=device, name=name, gender=gender, helper=helper)


def _setup(world: World, hero: Entity, device: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved quiet play in {world.setting.place}."
    )
    world.say(
        f"One morning, {hero.id} found {device.phrase} on the table, but frost had made it cold and stuck."
    )
    world.para()
    world.say(
        f"{hero.id} wanted to use the {device.label} right away, because the screen looked fun."
    )
    helper.memes["patience"] += 1
    world.say(
        f"But {hero.id}'s {helper.label} said, \"Let's be careful and brave, and fix it the right way.\""
    )
    hero.memes["worry"] += 1
    hero.memes["bravery"] += 1


def _fix(world: World, hero: Entity, device: Entity, helper: Entity, devcfg: Device) -> None:
    world.para()
    world.say(
        f"{hero.id} took a breath, grabbed a soft cloth, and chose bravery over rushing."
    )
    device.meters["wiped"] += 1
    device.meters["icy"] = 0
    device.meters["cold"] = max(0.0, device.meters["cold"] - 1)
    world.say(f"Together they chose to {devcfg.fix}.")
    world.say(f"Then they {devcfg.warm_step}.")
    helper.memes["pride"] += 1
    hero.memes["patience"] += 1
    hero.memes["pride"] += 1
    device.meters["powered"] += 1
    world.say(
        f"At last, {devcfg.final_image}, and {hero.id} smiled because the brave choice worked."
    )
    world.say(
        f"{hero.id} sat beside {hero.pronoun('possessive')} {helper.label} and used the {device.label} gently."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult", label=params.helper))
    device = world.add(
        Entity(
            id=params.device,
            kind="thing",
            type="device",
            label=DEVICES[params.device].label,
            phrase=DEVICES[params.device].phrase,
            owner=hero.id,
            caretaker=helper.id,
            meters={"cold": 1.0, "icy": 1.0, "wiped": 0.0, "powered": 0.0},
        )
    )
    world.facts.update(hero=hero, helper=helper, device=device, devcfg=DEVICES[params.device])
    _setup(world, hero, device, helper)
    _fix(world, hero, device, helper, DEVICES[params.device])
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    device: Entity = world.facts["device"]  # type: ignore[assignment]
    return [
        f"Write a short story for little kids about {hero.id}, frost, and a brave fix for an {device.label}.",
        f"Tell an Animal Story style tale where {hero.id} stays calm and brave in {world.setting.place}.",
        f"Write a gentle story about a child who chooses bravery instead of rushing when an {device.label} gets frosty.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    device: Entity = world.facts["device"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who found the frosty {device.label} in the playroom?",
            answer=f"{hero.id} found the frosty {device.label} in {world.setting.place}.",
        ),
        QAItem(
            question=f"What brave thing did {hero.id} do before using the {device.label}?",
            answer=f"{hero.id} took a breath and chose to fix the {device.label} with {helper.label} instead of rushing.",
        ),
        QAItem(
            question=f"How did the story end for the {device.label}?",
            answer=f"The frost was wiped away, the {device.label} warmed up, and {hero.id} could use it gently.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is frost?",
            answer="Frost is a thin, icy layer that can form on cold things or cold surfaces.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel nervous or want to rush.",
        ),
        QAItem(
            question="What is an iPad?",
            answer="An iPad is a small tablet computer with a screen you can tap to use apps, games, and pictures.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show good_story/2."))
        print(sorted(set(asp.atoms(model, "good_story"))))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        for place, device in valid_combos():
            params = StoryParams(place=place, device=device, name="Curt", gender="boy", helper="mom")
            samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = args.seed
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
