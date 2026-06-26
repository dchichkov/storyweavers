#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/prospector_kale_dialogue_cautionary_suspense_bedtime_story.py
=================================================================================================================

A small bedtime-story world about a prospector, a patch of kale, a cautious
night walk, and a harmless suspenseful misunderstanding.

Seed tale:
---
A sleepy prospector followed a moonlit trail behind the cottage, hoping the
shiny leaves in the garden meant gold. Instead, he found a patch of kale.
A child wanted to taste it at once, but the prospector warned that unknown
plants should be checked first. Together they waited, listened to the crickets,
and asked the gardener, who smiled and said the leaves were good to eat after
washing. The child learned to be patient, and the little garden felt safe again.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    edible: bool = False
    safe_after_wash: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "prospector"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the garden"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
    setting: Setting
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero_name: str
    child_name: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"kale"}),
    "backyard": Setting(place="the backyard", indoor=False, affords={"kale"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"kale"}),
}

HERO_NAMES = ["Milo", "Nina", "Theo", "Lina", "Owen", "Ivy"]
CHILD_NAMES = ["Pip", "Mina", "Jasper", "Bea", "Toby", "Rosa"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/2.
setting(garden). setting(backyard). setting(kitchen).
indoor(kitchen).
affords(garden,kale). affords(backyard,kale). affords(kitchen,kale).

valid(P, A) :- affords(P, A).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    return sorted((p, a) for p, s in SETTINGS.items() for a in s.affords)


def asp_verify() -> int:
    a, p = set(asp_valid()), set(python_valid())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> StoryState:
    setting = SETTINGS[params.place]
    world = StoryState(setting=setting)

    hero = world.add(Entity(
        id=params.hero_name, kind="character", type="prospector",
        traits=["sleepy", "careful"],
    ))
    child = world.add(Entity(
        id=params.child_name, kind="character", type="child",
        traits=["curious", "small"],
    ))
    gardener = world.add(Entity(
        id="Gardener", kind="character", type="gardener",
        traits=["gentle"],
    ))
    kale = world.add(Entity(
        id="kale", type="kale", label="kale", phrase="a patch of kale",
        owner=gardener.id, caretaker=gardener.id, edible=True, safe_after_wash=True,
    ))

    # Act 1
    world.say(
        f"On a quiet bedtime evening, {hero.id} was a sleepy prospector who loved moonlit walks."
    )
    world.say(
        f'{hero.id} peeked at the shiny leaves and whispered, "Could that be gold?"'
    )
    world.say(
        f'{child.id} tiptoed beside {hero.id} and asked, "Is it treasure, or is it supper?"'
    )

    # Act 2
    world.para()
    world.say(
        f"Near {world.setting.place}, the leaves gleamed in the dark, and the night felt very still."
    )
    world.say(
        f"{child.id} reached for the leaves at once, but {hero.id} lifted a hand and said, "
        f'"Wait first. Some plants are safe, and some are not."'
    )
    child.memes["impulse"] = 1
    hero.memes["caution"] = 1
    world.facts["tension"] = True
    world.facts["danger"] = True
    world.say(
        f"The crickets kept chirping while everyone listened for footsteps in the grass."
    )

    # Act 3
    world.para()
    world.say(
        f"Then the gardener came with a lantern and smiled. "
        f'"It is kale," {gardener.id} said. "It is good to eat after you wash it."'
    )
    world.say(
        f"{child.id} breathed out, and {hero.id} laughed softly, relieved that the mystery was safe."
    )
    world.say(
        f"They carried the kale inside, washed it in a little bowl, and left the moonlit path peaceful again."
    )

    world.facts.update(
        hero=hero,
        child=child,
        gardener=gardener,
        kale=kale,
        place=params.place,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        'Write a bedtime story about a prospector who mistakes shiny kale for treasure.',
        f"Tell a gentle suspense story where {f['hero'].id} warns {f['child'].id} to check a plant before tasting it.",
        f'Write a child-friendly story set in {f["place"]} with a dialogue about whether a leafy patch is safe.',
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    child = f["child"]
    gardener = f["gardener"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the sleepy prospector in the story?",
            answer=f"The sleepy prospector was {hero.id}. {hero.id} walked by moonlight and watched the shiny leaves carefully.",
        ),
        QAItem(
            question=f"What did {child.id} want to do when they found the shiny leaves?",
            answer=f"{child.id} wanted to taste the leaves at once, but {hero.id} said to wait and check first.",
        ),
        QAItem(
            question=f"Why did everyone stop worrying at {place}?",
            answer=f"Everyone stopped worrying because the gardener arrived with a lantern and said the leaves were kale, which was safe after washing.",
        ),
        QAItem(
            question=f"What did they do with the kale at the end?",
            answer=f"They carried the kale inside and washed it in a little bowl before bedtime.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is kale?",
            answer="Kale is a leafy green vegetable that people can wash and eat.",
        ),
        QAItem(
            question="Why should someone check a plant before tasting it?",
            answer="Someone should check a plant first because some wild plants are not safe to eat, and a careful adult can help tell the difference.",
        ),
        QAItem(
            question="What is a prospector?",
            answer="A prospector is a person who looks for valuable things like gold or minerals.",
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


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.edible:
            bits.append("edible=True")
        if e.safe_after_wash:
            bits.append("safe_after_wash=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    hero_name = args.name or rng.choice(HERO_NAMES)
    child_name = args.child or rng.choice(CHILD_NAMES)
    if hero_name == child_name:
        child_name = rng.choice([n for n in CHILD_NAMES if n != hero_name])
    return StoryParams(place=place, hero_name=hero_name, child_name=child_name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a prospector, kale, caution, and suspense."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--child")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp_valid()
        print(f"{len(model)} valid combinations:\n")
        for place, act in model:
            print(f"  {place:10} {act}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [(p, f"{p.title()}Prospector", f"{p.title()}Child") for p in SETTINGS]
        for place, hero_name, child_name in combos:
            params = StoryParams(place=place, hero_name=hero_name, child_name=child_name)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
