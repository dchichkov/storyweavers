#!/usr/bin/env python3
"""
A tiny slice-of-life puppet theater story world with foreshadowing and humor.

Seed tale:
A child helps at a puppet theater. A puppet's string snags, a hand gets a tiny
scratch, and a bandage appears just in time. A glove becomes part of the stage
trick, and the show ends with laughter and a small saved performance.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the puppet theater"
    affordances: set[str] = field(default_factory=lambda: {"show", "rehearse", "fix_puppet"})


@dataclass
class StoryParams:
    name: str
    role: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


ROLES = {
    "usher": "usher",
    "helper": "helper",
    "kid": "kid",
}

NAMES = ["Mina", "Rory", "Tess", "Owen", "Nina", "Pia", "Leo", "Jules"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Puppet theater slice-of-life story world.")
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper", choices=["friend", "parent", "teacher"])
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
    role = args.role or rng.choice(list(ROLES))
    helper = args.helper or rng.choice(["friend", "parent", "teacher"])
    name = args.name or rng.choice(NAMES)
    return StoryParams(name=name, role=role, helper=helper)


def _maybe_bandage_needed(world: World, child: Entity, puppet: Entity, glove: Entity) -> bool:
    # foreshadowing gate: the glove is a clue that the puppet string will snag
    return glove.meters.get("loose", 0) > 0.5 or puppet.meters.get("snagged", 0) > 0.5


def tell(world: World, params: StoryParams) -> World:
    child = world.add(Entity(id="child", kind="character", type="kid", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    puppet = world.add(Entity(id="puppet", type="puppet", label="fox puppet", phrase="a fox puppet with bright ears"))
    glove = world.add(Entity(id="glove", type="glove", label="glove", phrase="a soft glove with a tiny seam"))
    bandage = world.add(Entity(id="bandage", type="bandage", label="bandage", phrase="a small bandage with stars"))

    child.memes["curiosity"] = 1.0
    puppet.meters["ready"] = 1.0
    glove.meters["loose"] = 1.0

    world.say(f"{child.label} spent a quiet afternoon at the puppet theater with {params.helper}.")
    world.say(f"The stage smelled like old curtains and warm dust, and {puppet.phrase} waited on the table.")
    world.say(f"On the bench nearby sat {glove.phrase}; it looked like it belonged to a grown-up, but it was really for the puppet trick.")

    world.para()
    world.say(f"{child.label} wanted to help with the show, so {child.pronoun()} slipped on the glove and tried the puppet's waving hand.")
    if _maybe_bandage_needed(world, child, puppet, glove):
        puppet.meters["snagged"] = 1.0
        child.meters["scratch"] = 1.0
        world.say("The glove's finger caught on a thread, and the fox puppet gave a ridiculous little sneeze of felt.")
        world.say(f"{params.helper.capitalize()} laughed first, then noticed a tiny scratch and brought out the bandage before it could sting.")
        bandage.meters["used"] = 1.0
        child.memes["relief"] = 1.0
        puppet.memes["saved"] = 1.0
    else:
        world.say("Nothing snagged, but the glove still made the puppet wave in a very serious, very funny way.")

    world.para()
    world.say(f"After that, {child.label} pressed the bandage on carefully and tried again, slower this time.")
    world.say(f"The fox puppet bowed, the glove behaved, and the little show went on without any more trouble.")
    world.say(f"At the end, {child.label} and {params.helper} laughed at how the smallest bandage could save the biggest pretend adventure.")

    world.facts.update(
        child=child,
        helper=helper,
        puppet=puppet,
        glove=glove,
        bandage=bandage,
        foreshadowing=True,
        humor=True,
        setting=world.setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        "Write a gentle slice-of-life story set in a puppet theater where a glove becomes part of a playful show.",
        f"Tell a child-friendly story about {child.label} helping at the puppet theater, with a small problem and a funny fix.",
        "Write a short story that includes a bandage, a glove, and a puppet show with a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Where did {child.label} spend the afternoon?",
            answer=f"{child.label} spent the afternoon at the puppet theater with {helper.label}.",
        ),
        QAItem(
            question=f"What small problem happened with the glove?",
            answer="The glove's finger caught on a thread, and the puppet made a silly sneeze before the problem was fixed.",
        ),
        QAItem(
            question="What helped the scratch feel better?",
            answer="A small bandage helped the scratch feel better right away.",
        ),
        QAItem(
            question=f"How did the story end for {child.label}?",
            answer=f"{child.label} kept helping, the puppet show went on, and everyone laughed at the funny little fix.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a puppet theater?",
            answer="A puppet theater is a place where people perform stories with puppets on a small stage.",
        ),
        QAItem(
            question="What is a bandage for?",
            answer="A bandage covers a small cut or scratch so it can feel protected and heal.",
        ),
        QAItem(
            question="Why might a glove be useful in a puppet show?",
            answer="A glove can help someone move a puppet's hand or keep a hand clean while handling props.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/2.
place(theater).
feature(foreshadowing).
feature(humor).
setting(puppet_theater).

valid(bandage, glove).
valid(glove, bandage).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "puppet_theater"),
        asp.fact("place", "theater"),
        asp.fact("feature", "foreshadowing"),
        asp.fact("feature", "humor"),
        asp.fact("seed_word", "bandage"),
        asp.fact("seed_word", "glove"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = {("bandage", "glove"), ("glove", "bandage")}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python ({len(asp_set)} pairs).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("clingo:", sorted(asp_set))
    print("python:", sorted(py_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(World(Setting()), params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mina", role="kid", helper="parent"),
            StoryParams(name="Rory", role="usher", helper="friend"),
            StoryParams(name="Tess", role="helper", helper="teacher"),
        ]
        samples = [generate(p) for p in curated]
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
