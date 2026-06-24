#!/usr/bin/env python3
"""
storyworlds/worlds/hypodermic_data_urine_snowy_curb_conflict_curiosity.py
========================================================================

A small standalone story world for a rhyming, child-facing safety story set on
a snowy curb, built from the seed words: hypodermic, data, urine.

Premise:
- A curious child notices a dropped clinic kit on a snowy curb.
- The kit contains a hypodermic, a data slip, and a urine sample cup.
- Curiosity pulls the child closer; Conflict rises when an adult stops them.
- The adult explains the danger, calls the clinic, and returns the kit safely.

The world tracks physical meters and emotional memes, then renders a complete
story with a clear beginning, middle turn, and ending image.

This file follows the storyworld contract:
- standalone stdlib script
- imports results eagerly
- lazy ASP import in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    weather: str
    setting_word: str


@dataclass
class KitItem:
    id: str
    label: str
    phrase: str
    safe_note: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    adult_name: str
    adult_type: str
    kit: str
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


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "snowy_curb"),
             asp.fact("contains", "kit", "hypodermic"),
             asp.fact("contains", "kit", "data"),
             asp.fact("contains", "kit", "urine")]
    return "\n".join(lines)


ASP_RULES = r"""
contains_important(kit) :- contains(kit, hypodermic), contains(kit, data), contains(kit, urine).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show contains_important/1."))
    return sorted(set(asp.atoms(model, "contains_important")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP and Python match ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" python-only:", sorted(py - cl))
    print(" clingo-only:", sorted(cl - py))
    return 1


SETTING = Setting(place="a snowy curb", weather="snowy", setting_word="snowy curb")
KITS = {
    "clinic_kit": KitItem(
        id="clinic_kit",
        label="clinic kit",
        phrase="a small clinic kit",
        safe_note="It should stay with the clinic",
        tags={"hypodermic", "data", "urine"},
    )
}


def valid_combos() -> list[tuple[str, str]]:
    return [("snowy_curb", "clinic_kit")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming safety story world on a snowy curb.")
    ap.add_argument("--place", choices=["snowy_curb"])
    ap.add_argument("--kit", choices=list(KITS))
    ap.add_argument("--name")
    ap.add_argument("--adult")
    ap.add_argument("--type", dest="child_type", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=["mother", "father"])
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
    if args.place and args.place != "snowy_curb":
        raise StoryError("(No valid story for that place.)")
    if args.kit and args.kit not in KITS:
        raise StoryError("(No valid story for that kit.)")
    place, kit = rng.choice(combos)
    return StoryParams(
        place=place,
        child_name=args.name or rng.choice(["Nina", "Milo", "Tess", "Owen"]),
        child_type=args.child_type or rng.choice(["girl", "boy"]),
        adult_name=args.adult or rng.choice(["Mom", "Dad", "Aunt Jo", "Mr. Lee"]),
        adult_type=args.adult_type or rng.choice(["mother", "father"]),
        kit=kit,
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    kid = world.add(Entity(
        id=params.child_name, kind="character", type=params.child_type, role="child",
        meters={"steps": 0.0}, memes={"curiosity": 0.0, "conflict": 0.0, "relief": 0.0},
    ))
    adult = world.add(Entity(
        id=params.adult_name, kind="character", type=params.adult_type, role="adult",
        meters={"steps": 0.0}, memes={"care": 1.0, "conflict": 0.0, "relief": 0.0},
    ))
    kit = KITS[params.kit]
    world.facts.update(child=kid, adult=adult, kit=kit, setting=SETTING)

    world.say(f"{kid.id} walked by a snowy curb, where the white flakes swirled in a curbside blur.")
    world.say(f"Near the slush sat {kit.phrase}, and {kid.id} felt a bright little stir.")
    kid.memes["curiosity"] += 1
    world.say(f'{kid.id} leaned in close and whispered, "What could this be in the icy air?"')
    world.para()
    world.say(f"But inside were a hypodermic, some data, and a cup of urine to share.")
    kid.memes["conflict"] += 1
    adult.memes["conflict"] += 1
    world.say(f'{adult.id} said, "Stop right there; those are not for play, my dear."')
    world.say(f"\"We must not touch the needle, the notes, or the sample here.\"")
    world.para()
    kid.memes["conflict"] = 0.0
    kid.memes["relief"] += 1
    adult.memes["relief"] += 1
    world.say(f"{kid.id} nodded and stepped back fast, with careful little feet.")
    world.say(f"{adult.id} called the clinic, and soon the lost kit was made complete.")
    world.say(f"They carried it inside, where it belonged, out of the snowy street.")
    world.say(f"And {kid.id} laughed at the drifting snow, safe, snug, and sweet.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"].id
    kit = f["kit"].label
    return [
        f'Write a rhyming story for a small child about {child} on a snowy curb who finds {kit}.',
        f"Tell a gentle caution story with the words hypodermic, data, and urine, where curiosity leads to conflict and a grown-up helps.",
        f"Make a short rhyming story set on a snowy curb where a child spots a clinic kit and then does the safe thing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, kit = f["child"], f["adult"], f["kit"]
    return [
        QAItem(
            question=f"What did {child.id} find by the snowy curb?",
            answer=f"{child.id} found {kit.phrase} by the snowy curb.",
        ),
        QAItem(
            question=f"Why did {child.id} feel curious?",
            answer=f"{child.id} felt curious because the kit looked new and interesting in the snow.",
        ),
        QAItem(
            question=f"What did {adult.id} say about the kit?",
            answer=f"{adult.id} said not to touch it and explained that the hypodermic, data, and urine were not for play.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The kit went back to the clinic, and {child.id} stayed safe in the snowy curbside air.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hypodermic?",
            answer="A hypodermic is a sharp medical needle used by trained grown-ups and doctors.",
        ),
        QAItem(
            question="What is data?",
            answer="Data is information, like notes or facts that help people learn and keep track of things.",
        ),
        QAItem(
            question="What is urine?",
            answer="Urine is a liquid the body makes and sends away; doctors may test it to learn about health.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [StoryParams(place="snowy_curb", child_name="Nina", child_type="girl", adult_name="Mom", adult_type="mother", kit="clinic_kit")]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show contains_important/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show contains_important/1."))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
