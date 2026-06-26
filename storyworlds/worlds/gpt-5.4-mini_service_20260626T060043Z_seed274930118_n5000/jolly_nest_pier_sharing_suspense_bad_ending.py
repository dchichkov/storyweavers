#!/usr/bin/env python3
"""
A small animal-story world set on a pier, with sharing, suspense, and a bad ending.

Seed tale:
A jolly little gull found a nest near the pier. It wanted to keep every shiny bit
for itself, but another animal needed help. The two tried to share a tiny catch
while waves slapped the posts. In the end, the nest was not safe, and the sharing
did not save the day.

This script turns that premise into a simulated world with physical meters and
emotional memes, plus an ASP twin for the validity gate.
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

PIER_THINGS = {"pier", "rope", "bucket", "shell", "fish", "nest", "wave"}
SPECIES = ["gull", "crab", "otter", "seal"]
NAMES = {
    "gull": ["Nori", "Pip", "Momo", "Lulu"],
    "crab": ["Clack", "Ria", "Bibi", "Toto"],
    "otter": ["Suri", "Mina", "Kiko", "Roo"],
    "seal": ["Bolo", "Nina", "Fuzz", "Dodo"],
}


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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["wet", "safe", "danger", "lost", "full"]:
            self.meters.setdefault(k, 0.0)
        for k in ["jolly", "hope", "worry", "shared", "suspense", "fear", "sad"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"gull", "crab", "otter", "seal"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pier"
    affords: set[str] = field(default_factory=lambda: {"sharing", "suspense"})


@dataclass
class StoryParams:
    animal: str
    partner: str
    prize: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        return w


def story_is_reasonable(params: StoryParams) -> bool:
    return params.animal in SPECIES and params.partner in SPECIES and params.prize in {"nest", "fish", "shell", "rope"}


def reasonability_gate(params: StoryParams) -> None:
    if not story_is_reasonable(params):
        raise StoryError("The little animal story needs a real animal, a partner, and a pier-safe prize.")


def _share(world: World, hero: Entity, partner: Entity, prize: Entity) -> None:
    hero.memes["shared"] += 1
    partner.memes["shared"] += 1
    prize.meters["full"] += 1
    world.say(f"{hero.id} slid the {prize.label} closer so {partner.id} could have a turn too.")


def _suspense(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["suspense"] += 1
    hero.memes["worry"] += 1
    prize.meters["wet"] += 1
    world.say("Then the waves tapped the pier posts harder and harder.")
    world.say(f"The little {prize.label} wobbled near the edge, and everyone held still.")


def _bad_ending(world: World, hero: Entity, partner: Entity, prize: Entity, nest: Entity) -> None:
    prize.meters["lost"] += 1
    nest.meters["safe"] = 0
    nest.meters["lost"] += 1
    hero.memes["sad"] += 1
    partner.memes["sad"] += 1
    world.say(f"A bigger wave splashed up, and the {prize.label} slipped away under the boards.")
    world.say(f"The {nest.label} stayed on the pier, but it was no longer snug or safe.")
    world.say(f"{hero.id} and {partner.id} looked at the water, quiet and disappointed.")


def tell(params: StoryParams) -> World:
    reasonability_gate(params)
    world = World(Setting())
    hero = world.add(Entity(id=params.animal, kind="character", type=params.animal, label=params.animal))
    partner = world.add(Entity(id=f"{params.partner}-friend", kind="character", type=params.partner, label=params.partner))
    prize = world.add(Entity(id=params.prize, type=params.prize, label=params.prize, phrase=f"a little {params.prize}"))
    nest = world.add(Entity(id="nest", type="nest", label="nest", phrase="a cozy nest"))

    world.facts.update(hero=hero, partner=partner, prize=prize, nest=nest, setting=world.setting)

    hero.memes["jolly"] += 1
    world.say(f"On the pier, a jolly little {hero.type} found a {nest.label} tucked between the ropes.")
    world.say(f"It liked a shiny {prize.label} and wanted to keep it close all day.")

    world.para()
    world.say(f"A {partner.type} came by, and the two animals tried to share the {prize.label}.")
    _share(world, hero, partner, prize)
    world.say(f"That made the day feel kinder for a moment.")

    world.para()
    _suspense(world, hero, prize)
    world.say("Both animals watched the water, hoping the pier would stay calm.")

    world.para()
    _bad_ending(world, hero, partner, prize, nest)

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short animal story for a young child set on a pier with a jolly mood, a nest, sharing, suspense, and a bad ending.',
        f"Tell a tiny story about a {f['hero'].type} and a {f['partner'].type} on the pier who try to share a {f['prize'].label} near a nest.",
        "Make the story gentle, concrete, and ending sadly when the waves win.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, partner, prize, nest = f["hero"], f["partner"], f["prize"], f["nest"]
    return [
        QAItem(
            question=f"Where did {hero.id} find the nest?",
            answer="It was on the pier, tucked close to the ropes and boards.",
        ),
        QAItem(
            question=f"What did {hero.id} and the {partner.type} try to do with the {prize.label}?",
            answer=f"They tried to share the {prize.label} so both animals could have a turn.",
        ),
        QAItem(
            question="What made the story feel suspenseful?",
            answer="The waves kept tapping harder and the little prize wobbled near the edge.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly: the {prize.label} slipped away, and the nest was no longer safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pier?",
            answer="A pier is a long wooden path that stretches out over water.",
        ),
        QAItem(
            question="Why can waves be dangerous near a pier?",
            answer="Waves can splash hard, make things slippery, and push small things into the water.",
        ),
        QAItem(
            question="What is a nest for?",
            answer="A nest is a cozy place where some animals rest, sleep, or keep their eggs safe.",
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


ASP_RULES = r"""
chosen_story(A,B,C) :- animal(A), partner(B), prize(C).
valid_story(A,B,C) :- chosen_story(A,B,C), animal_ok(A), animal_ok(B), prize_ok(C), setting(pier).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "pier")]
    for a in SPECIES:
        lines.append(asp.fact("animal", a))
        lines.append(asp.fact("animal_ok", a))
    for p in SPECIES:
        lines.append(asp.fact("partner", p))
        lines.append(asp.fact("animal_ok", p))
    for z in ["nest", "fish", "shell", "rope"]:
        lines.append(asp.fact("prize", z))
        lines.append(asp.fact("prize_ok", z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = {(a, b, c) for a in SPECIES for b in SPECIES for c in ["nest", "fish", "shell", "rope"]}
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world on a pier with sharing and suspense.")
    ap.add_argument("--animal", choices=SPECIES)
    ap.add_argument("--partner", choices=SPECIES)
    ap.add_argument("--prize", choices=["nest", "fish", "shell", "rope"])
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
    animal = args.animal or rng.choice(SPECIES)
    partner = args.partner or rng.choice([s for s in SPECIES if s != animal])
    prize = args.prize or rng.choice(["nest", "fish", "shell", "rope"])
    params = StoryParams(animal=animal, partner=partner, prize=prize)
    reasonability_gate(params)
    return params


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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories")
        for row in stories:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for a in SPECIES:
            for b in SPECIES:
                if b == a:
                    continue
                for p in ["nest", "fish", "shell", "rope"]:
                    samples.append(generate(StoryParams(animal=a, partner=b, prize=p)))
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
