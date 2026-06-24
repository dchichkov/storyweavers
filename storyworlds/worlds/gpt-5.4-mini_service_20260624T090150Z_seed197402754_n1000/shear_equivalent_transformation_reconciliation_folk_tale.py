#!/usr/bin/env python3
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "queen"}
        male = {"boy", "man", "father", "brother", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    name: str
    role: str
    companion: str
    seed: Optional[int] = None


@dataclass
class Grove:
    name: str = "the old grove"
    hill: str = "the green hill"
    path: str = "the stone path"
    sheepfold: str = "the sheepfold"


@dataclass
class World:
    setting: Grove
    entities: dict[str, Entity] = field(default_factory=dict)
    story_bits: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.story_bits.append(text)

    def para(self) -> None:
        if self.story_bits and self.story_bits[-1] != "":
            self.story_bits.append("")

    def render(self) -> str:
        paras: list[str] = []
        buf: list[str] = []
        for bit in self.story_bits:
            if bit == "":
                if buf:
                    paras.append(" ".join(buf))
                    buf = []
            else:
                buf.append(bit)
        if buf:
            paras.append(" ".join(buf))
        return "\n\n".join(paras)


SETTINGS = {"grove": Grove()}
NAMES = ["Mara", "Ned", "Tova", "Pip", "Bram", "Lina", "Eli", "Runa"]
ROLES = {"shepherd": "shepherd", "weaver": "weaver", "goatherd": "goatherd", "spinner": "spinner"}
COMPANIONS = {
    "sheep": "a woolly sheep",
    "goat": "a stubborn goat",
    "cloak": "a plain cloak",
    "basket": "a reed basket",
}


def valid_combos() -> list[tuple[str, str]]:
    return [("grove", role) for role in ROLES]


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "grove")]
    for role in ROLES:
        lines.append(asp.fact("role", role))
        lines.append(asp.fact("affords", "grove", role))
    lines.append(asp.fact("theme", "shear"))
    lines.append(asp.fact("theme", "equivalent"))
    return "\n".join(lines)


ASP_RULES = r"""
role_story(G,R) :- setting(G), role(R), affords(G,R).
#show role_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show role_story/2."))
    return sorted(set(asp.atoms(model, "role_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale about shear, equivalent, transformation, and reconciliation.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=list(ROLES))
    ap.add_argument("--companion", choices=list(COMPANIONS))
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
    combos = valid_combos()
    if args.role and ("grove", args.role) not in combos:
        raise StoryError("No valid combination matches the given options.")
    role = args.role or rng.choice(list(ROLES))
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(list(COMPANIONS))
    return StoryParams(name=name, role=role, companion=companion)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS["grove"])
    hero = world.add(Entity(id=params.name, kind="character", type="person"))
    elder = world.add(Entity(id="Elder", kind="character", type="woman", label="the elder"))
    comp = world.add(Entity(id="Companion", kind="thing", type=params.companion, label=COMPANIONS[params.companion]))
    comp.worn_by = hero.id

    shear_meter = 0.0
    equivalent_meter = 0.0
    transform_meter = 0.0
    reconcile_meter = 0.0

    world.say(f"Long ago, in {world.setting.name}, there lived {params.name}, a {params.role} who kept to the old paths.")
    world.say(f"{params.name} had {comp.label} for a companion, and {comp.pronoun('subject')} was as dear as kin.")
    world.para()
    world.say(f"Each spring, the elders said it was time to shear the flock, and the wool was taken into the little house by the hill.")
    world.say(f"{params.name} found one bundle of wool that looked as soft as any cloud, and {comp.pronoun('subject')} feared it would be lost forever.")
    shear_meter += 1.0
    world.facts["shear"] = True
    world.facts["equivalent"] = True
    world.para()
    world.say(f"Then {params.name} had a wise thought: what if the wool could be made equivalent to a warmer gift instead of lying useless in a sack?")
    world.say(f"{params.name} spun the wool, wove it with a red thread, and by dusk turned it into a small cloak fit for the cold road.")
    transform_meter += 1.0
    equivalent_meter += 1.0
    world.para()
    world.say(f"When the little cloak was done, the elder smiled, for the wool had changed its shape but not its worth.")
    world.say(f"The elder and {params.name} shared the cloak with {comp.label}, and the companion nuzzled close, no longer restless.")
    reconcile_meter += 1.0
    world.say(f"So the sheepfold grew quiet again, and the grove kept its warm secret: a thing may be transformed and still be equivalent in kindness.")

    world.facts.update(hero=hero, elder=elder, companion=comp)
    story = world.render()
    prompts = [
        "Write a gentle folk tale about shear, equivalent, and a change of heart.",
        f"Tell a short story where {params.name} helps in the grove and turns wool into something new.",
        "Write a folk tale with a transformation and a reconciliation at the end.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.name} do with the wool after it was shorn?",
            answer=f"{params.name} spun and wove the wool into a small cloak, turning it into something useful and warm.",
        ),
        QAItem(
            question="Why was the wool called equivalent to a gift?",
            answer="Because even though the wool changed shape, it kept its worth and became useful in a new way.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The elder, the hero, and the companion were at peace again, with the transformed cloak keeping someone warm.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does shear mean?",
            answer="To shear means to cut off wool or hair from an animal, usually so the fleece can be collected.",
        ),
        QAItem(
            question="What does equivalent mean?",
            answer="Equivalent means equal in worth, even if two things look different.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is when something changes into a new form or state.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were apart or upset become peaceful with one another again.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"  {e.id}: {e.type} {' '.join(bits)}")
        print(f"  facts: {sample.world.facts}")
    if qa:
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show role_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, role in enumerate(ROLES):
            params = StoryParams(name=NAMES[i % len(NAMES)], role=role, companion=list(COMPANIONS)[i % len(COMPANIONS)])
            params.seed = base_seed + i
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
