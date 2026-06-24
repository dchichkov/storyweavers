#!/usr/bin/env python3
"""
storyworlds/worlds/peony_specifics_kindness_rhyming_story.py
=============================================================

A small story world about a peony, careful specifics, and kindness.

Premise:
- A child loves a peony in a garden bed.
- The child wants to gather "specifics" for a flower craft: petals, ribbon, and a note.
- A parent or gardener worries that rushing will harm the peony.
- A kinder plan is to ask first, trim only fallen petals, and make a gift that keeps the flower safe.

The world simulates physical and emotional state:
- meters: stem, bloom, petals, water, trim, ribbon, paper, tidy
- memes: joy, worry, pressure, patience, kindness, pride

The prose is written in a light rhyming story style, but state drives what happens:
- the child may fuss, pause, ask, help, and then choose a respectful plan.
- if the peony would be damaged, the parent/gardener can redirect the child.

This file is standalone and follows the Storyweavers contract.
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
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Garden:
    place: str = "the garden"
    fragrance: str = "sweet"
    breeze: str = "soft"


@dataclass
class PeonySpec:
    color: str
    scent: str
    stage: str
    word: str = "peony"


@dataclass
class KindnessPlan:
    ask_first: str
    safe_help: str
    keeps_peony_safe: bool = True


class World:
    def __init__(self, garden: Garden) -> None:
        self.garden = garden
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
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

        clone = World(self.garden)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str
    peony_color: str
    peony_scent: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mia", "Lily", "Zoe", "Nora", "Ava", "June"],
    "boy": ["Leo", "Finn", "Theo", "Max", "Owen", "Sam"],
}
PARENTS = ["mother", "father"]
COLORS = ["pink", "white", "rose-red", "soft coral"]
SCENTS = ["sweet", "fragrant", "mild", "honeyed"]
PLACES = ["the garden", "the backyard garden", "the flower patch"]


def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def setup_line(garden: Garden, peony: PeonySpec) -> str:
    return (
        f"In {garden.place}, where the breeze was light, "
        f"a {peony.color} peony bloomed in sight."
    )


def introduce(hero: Entity, parent: Entity, peony: Entity, world: World) -> None:
    world.say(
        f"{hero.noun().capitalize()} was a little {hero.type} with a bright, kind grin, "
        f"and {hero.pronoun('possessive')} {parent.noun()} watched the garden within."
    )
    world.say(
        f"Near the stone path stood {peony.phrase}, all soft and neat, "
        f"with petals like pillows and a {world.garden.fragrance} smell sweet."
    )


def love_peony(hero: Entity, peony: Entity, world: World) -> None:
    hero.memes["joy"] = hero.meme("joy") + 1
    world.say(
        f"{hero.noun().capitalize()} loved that peony so bright, so grand, "
        f"and wanted to make a craft by hand."
    )


def want_specifics(hero: Entity, peony: Entity, world: World) -> None:
    hero.memes["pressure"] = hero.meme("pressure") + 1
    world.say(
        f"{hero.noun().capitalize()} wanted specifics, with a careful plan: "
        f"some petals, a ribbon, and a note if {hero.pronoun()} can."
    )


def predict_damage(world: World, peony: Entity) -> bool:
    sim = world.copy()
    sim.get("hero").meters["pluck"] = sim.get("hero").meter("pluck") + 1
    sim.get("peony").meters["petals"] = max(0, sim.get("peony").meter("petals") - 1)
    return sim.get("peony").meter("petals") < peony.meter("petals")


def warn(parent: Entity, hero: Entity, peony: Entity, world: World) -> bool:
    if not predict_damage(world, peony):
        return False
    parent.memes["worry"] = parent.meme("worry") + 1
    world.facts["worry_reason"] = "the peony could lose petals too soon"
    world.say(
        f'"Careful now," said {parent.noun()}, kind and keen. '
        f'"If you pull too much, the peony will lose its sheen."'
    )
    return True


def fuss(hero: Entity, world: World) -> None:
    hero.memes["pressure"] = hero.meme("pressure") + 1
    hero.memes["patience"] = hero.meme("patience") + 0.5
    world.say(
        f"{hero.noun().capitalize()} gave a small sigh, then paused in place; "
        f"{hero.pronoun().capitalize()} wanted the craft, but slowed the pace."
    )


def offer_kindness(parent: Entity, hero: Entity, peony: Entity, plan: KindnessPlan, world: World) -> None:
    hero.memes["kindness"] = hero.meme("kindness") + 1
    parent.memes["kindness"] = parent.meme("kindness") + 1
    world.say(
        f'"Let’s ask first," said {parent.noun()}, warm as a song. '
        f'"We can be gentle, and still make it strong."'
    )
    world.say(
        f'They chose {plan.safe_help}, a kinder way, '
        f'and kept the peony safe that day.'
    )


def do_safe_help(hero: Entity, peony: Entity, world: World) -> None:
    hero.memes["joy"] = hero.meme("joy") + 1
    hero.memes["pride"] = hero.meme("pride") + 1
    peony.meters["water"] = peony.meter("water") + 1
    peony.meters["tidy"] = peony.meter("tidy") + 1
    world.say(
        f"{hero.noun().capitalize()} helped water the roots with a tiny tin cup, "
        f"and watched the peony drink the drops up."
    )


def gather_safe_specifics(hero: Entity, peony: Entity, world: World) -> None:
    peony.meters["petals"] = peony.meter("petals")  # unchanged
    hero.meters["paper"] = hero.meter("paper") + 1
    hero.meters["ribbon"] = hero.meter("ribbon") + 1
    world.say(
        f"Instead of plucking the bloom in haste, {hero.noun()} picked up a fallen petal with taste, "
        f"then tied on a ribbon and wrote a sweet line, "
        f"so the peony stayed lovely and fine."
    )


def ending_image(hero: Entity, parent: Entity, peony: Entity, world: World) -> None:
    world.say(
        f"At sunset, {hero.noun()} smiled by the bed; "
        f"the peony stood glowing, pink and red. "
        f"{hero.pronoun().capitalize()} had specifics, and kindness too, "
        f"and the garden felt brighter through and through."
    )


def build_garden_story(world: World, hero: Entity, parent: Entity, peony: Entity) -> None:
    world.say(setup_line(world.garden, PeonySpec(peony.meters.get("color", 0) and "pink" or "pink", "sweet", "blooming")))
    introduce(hero, parent, peony, world)
    world.para()
    love_peony(hero, peony, world)
    want_specifics(hero, peony, world)
    warned = warn(parent, hero, peony, world)
    if warned:
        fuss(hero, world)
    world.para()
    plan = KindnessPlan(
        ask_first="ask before picking",
        safe_help="watering the roots and using a fallen petal",
    )
    offer_kindness(parent, hero, peony, plan, world)
    do_safe_help(hero, peony, world)
    gather_safe_specifics(hero, peony, world)
    world.para()
    ending_image(hero, parent, peony, world)


SETTINGS = {
    "garden": Garden(place="the garden", fragrance="sweet", breeze="soft"),
    "backyard": Garden(place="the backyard garden", fragrance="sweet", breeze="gentle"),
    "patch": Garden(place="the flower patch", fragrance="fragrant", breeze="mild"),
}


def valid_places() -> list[str]:
    return list(SETTINGS.keys())


def valid_names(gender: str) -> list[str]:
    return NAMES[gender]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming story world about a peony and kindness.")
    ap.add_argument("--place", choices=valid_places())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(valid_names(gender))
    parent = args.parent or rng.choice(PARENTS)
    place = args.place or rng.choice(valid_places())
    peony_color = rng.choice(COLORS)
    peony_scent = rng.choice(SCENTS)
    return StoryParams(
        name=name,
        gender=gender,
        parent=parent,
        place=place,
        peony_color=peony_color,
        peony_scent=peony_scent,
    )


def generate_world(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    peony = world.add(
        Entity(
            id="peony",
            kind="thing",
            type="flower",
            label="peony",
            phrase=f"a {params.peony_color} peony with a {params.peony_scent} scent",
        )
    )
    peony.meters["petals"] = 8
    peony.meters["water"] = 2
    peony.meters["tidy"] = 1
    peony.meters["color"] = 1

    build_garden_story(world, hero, parent, peony)
    world.facts = {
        "hero": hero,
        "parent": parent,
        "peony": peony,
        "params": params,
        "resolved": True,
    }
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a gentle rhyming story about a child named {p.name} who loves a {p.peony_color} peony.',
        f"Tell a short story where kindness helps {p.name} gather specifics for a flower craft without harming a peony.",
        f'Write a child-friendly garden story that includes the words "peony" and "specifics" and ends in a calm, caring way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    peony: Entity = f["peony"]
    return [
        QAItem(
            question=f"What flower did {params.name} care about in the garden?",
            answer=f"{params.name} cared about a peony, and it was {params.peony_color} with a {params.peony_scent} scent.",
        ),
        QAItem(
            question=f"Why did {params.parent} worry when {params.name} wanted specifics from the peony?",
            answer=f"{params.parent} worried because pulling too much could hurt the peony and make it lose petals too soon.",
        ),
        QAItem(
            question=f"How did {params.name} show kindness instead of picking the peony apart?",
            answer=f"{params.name} asked first, watered the roots, and used a fallen petal and a ribbon for the craft.",
        ),
        QAItem(
            question=f"How did the story end for {params.name} and the peony?",
            answer=f"It ended with {params.name} smiling beside the peony, which stayed safe, neat, and blooming.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    return [
        QAItem(
            question="What is a peony?",
            answer="A peony is a flowering plant with big, often fluffy blossoms.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means caring about someone or something and choosing gentle, helpful actions.",
        ),
        QAItem(
            question="Why should you ask before picking flowers in a garden?",
            answer="You should ask first because some flowers are being cared for, and touching them without permission can hurt them.",
        ),
        QAItem(
            question=f"What kind of place was {params.place} in this story?",
            answer=f"It was a garden place, with flowers, a soft breeze, and space for gentle care.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Declarative twin of the reasonableness gate:
% A flower is at risk if a child tries to pluck specifics from it.
at_risk(peony) :- wants_specifics(hero), flower(peony).

% A kindness plan is valid if it asks first and uses safe help.
kind_plan(ask_first, safe_help).
valid_story(peony, specifics, kindness) :- at_risk(peony), kind_plan(ask_first, safe_help).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("flower", "peony"),
            asp.fact("wants_specifics", "hero"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {("peony", "specifics", "kindness")}
    if atoms == expected:
        print("OK: ASP twin matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  asp:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Mia", gender="girl", parent="mother", place="garden", peony_color="pink", peony_scent="sweet"),
            StoryParams(name="Leo", gender="boy", parent="father", place="patch", peony_color="rose-red", peony_scent="fragrant"),
            StoryParams(name="Ava", gender="girl", parent="mother", place="backyard", peony_color="white", peony_scent="honeyed"),
        ]
        for p in curated:
            samples.append(generate_world(p))
        return samples
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(args.n * 20, 20):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate_world(params)
        i += 1
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world knowledge ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    samples = build_samples(args)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} peony kindness"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
