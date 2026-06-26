#!/usr/bin/env python3
"""
A small whodunit-style storyworld: a child visits a clinic, a certificate goes
missing, and the mystery is solved through kindness and dialogue.
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
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Clinic:
    place: str = "the clinic"


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, clinic: Clinic) -> None:
        self.clinic = clinic
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


GENDERED_NAMES = {
    "girl": ["Mina", "Lena", "Tia", "Ivy", "Nora", "Maya"],
    "boy": ["Evan", "Noah", "Owen", "Leo", "Milo", "Finn"],
}

HELPERS = ["nurse", "doctor", "receptionist", "parent", "friend"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld: certificate at a clinic.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENDERED_NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(name=name, gender=gender, helper=helper)


def _kindness_helps(world: World, child: Entity, helper: Entity, certificate: Entity) -> None:
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1.0)
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1.0
    certificate.location = "handed back"
    world.facts["solved"] = True
    world.say(
        f"{helper.label.capitalize()} smiled kindly and said, "
        f"\"Let's ask everyone carefully.\""
    )
    world.say(
        f"{child.id} listened, and the little mystery felt less heavy."
    )
    world.say(
        f"At last, the certificate was found tucked inside a clipboard, and "
        f"{child.id} held it with a proud exclamation."
    )


def tell_story(params: StoryParams) -> World:
    world = World(Clinic())
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"feet": 1.0},
        memes={"curious": 1.0, "worry": 1.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
        memes={"kindness": 1.0},
    ))
    certificate = world.add(Entity(
        id="Certificate",
        type="certificate",
        label="certificate",
        phrase="a bright yellow certificate",
        owner=child.id,
        location="missing",
    ))

    world.say(
        f"On a quiet morning, {child.id} went to {world.clinic.place} with "
        f"{child.pronoun('possessive')} bright yellow certificate."
    )
    world.say(
        f"Then the certificate was gone. {child.id} looked under a chair and "
        f"between two clipboards, but nothing answered."
    )
    world.para()
    world.say(
        f"{child.id} asked, \"Who moved my certificate?\" and the room grew still."
    )
    world.say(
        f"The {params.helper} said, \"Let's solve this together,\" and everyone began to talk."
    )
    world.say(
        f"One by one, the clues pointed to the clipboard near the front desk."
    )
    world.para()
    _kindness_helps(world, child, helper, certificate)

    world.facts.update(child=child, helper=helper, certificate=certificate)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    return [
        "Write a short whodunit story for young children about a missing certificate at a clinic.",
        f"Tell a gentle mystery where {child.id} asks for help, and {helper.label} solves the clue with kindness.",
        "Write a simple dialogue-filled story that ends with the missing certificate being found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"Where did {child.id} go at the start of the story?",
            answer=f"{child.id} went to the clinic at the start, carrying a certificate.",
        ),
        QAItem(
            question=f"Who helped solve the mystery?",
            answer=f"The {helper.type} helped solve the mystery by listening kindly and asking careful questions.",
        ),
        QAItem(
            question="What was missing?",
            answer="The certificate was missing for a while before it was found again.",
        ),
        QAItem(
            question="How did the story solve the mystery?",
            answer="The characters used dialogue, looked at the clues, and found the certificate inside a clipboard.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clinic?",
            answer="A clinic is a place where people go to get help from doctors or nurses.",
        ),
        QAItem(
            question="What is a certificate?",
            answer="A certificate is a paper that shows someone has earned or received something important.",
        ),
        QAItem(
            question="Why do people ask questions when solving a mystery?",
            answer="People ask questions to gather clues and understand what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
#show solved/0.
solved :- certificate_found.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("clinic", "clinic"),
        asp.fact("certificate", "certificate"),
        asp.fact("story_feature", "kindness"),
        asp.fact("story_feature", "dialogue"),
        asp.fact("story_feature", "mystery"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/0."))
    atoms = asp.atoms(model, "solved")
    if atoms == [()]:
        print("OK: ASP model includes solved.")
        return 0
    print("MISMATCH: ASP model did not include solved.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks in this storyworld.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        cur = [
            StoryParams(name="Mina", gender="girl", helper="nurse"),
            StoryParams(name="Leo", gender="boy", helper="doctor"),
            StoryParams(name="Ivy", gender="girl", helper="receptionist"),
        ]
        samples = [generate(p) for p in cur]
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
