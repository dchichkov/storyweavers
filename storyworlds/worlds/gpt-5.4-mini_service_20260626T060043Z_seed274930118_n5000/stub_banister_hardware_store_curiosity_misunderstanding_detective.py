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

ASP_RULES = r"""
% A curiosity story becomes valid when a curious detective can be confused by a
% hardware-store clue, but the clue must be explainable in the end.
valid_story(Place, Clue, Fix) :- store(Place), clue(Clue), fix(Fix),
                                 at_risk(Clue, Fix), resolves(Clue, Fix).
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the hardware store"


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


HARDWARE_STORE = Setting(place="the hardware store")

CURIOUS_TRAITS = ["curious", "sharp-eyed", "careful", "bright"]
HELPERS = {
    "manager": "the store manager",
    "worker": "the worker",
    "cashier": "the cashier",
}

CLUE_LABEL = "stub"
FIX_LABEL = "banister"
MISUNDERSTAND_LABEL = "misunderstanding"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective-story world in a hardware store.")
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


def _gender_ok(gender: str, name: str) -> bool:
    return bool(name)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Maya", "Leo", "Nina", "Owen", "Iris", "Finn"])
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(name=name, gender=gender, helper=helper)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("store", "hardware_store"),
        asp.fact("clue", "stub"),
        asp.fact("fix", "banister"),
        asp.fact("at_risk", "stub", "banister"),
        asp.fact("resolves", "stub", "banister"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("hardware_store", "stub", "banister")}
    cl = set(asp_valid())
    if py == cl:
        print("OK: clingo gate matches Python gate (1 story shape).")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def reasonableness_gate(params: StoryParams) -> None:
    if not _gender_ok(params.gender, params.name):
        raise StoryError("Invalid character setup.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.name.strip().lower() == "stub":
        raise StoryError("The detective name cannot be 'stub'; that word belongs to the clue.")
    if params.name.strip().lower() == "banister":
        raise StoryError("The detective name cannot be 'banister'; that word belongs to the fix.")


def build_world(params: StoryParams) -> World:
    world = World(setting=HARDWARE_STORE)
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=params.gender,
        label=params.name,
        phrase=f"young {params.gender} detective {params.name}",
        memes={"curiosity": 1.0, "confidence": 0.5},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="adult",
        label=HELPERS[params.helper],
        phrase=HELPERS[params.helper],
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="stub",
        label="stub",
        phrase="a little wooden stub",
        owner="banister",
    ))
    fix = world.add(Entity(
        id="fix",
        kind="thing",
        type="banister",
        label="banister",
        phrase="a sturdy banister by the stairs",
    ))
    world.facts.update(
        detective=detective, helper=helper, clue=clue, fix=fix, params=params
    )
    return world


def tell(world: World) -> None:
    d = world.facts["detective"]
    h = world.facts["helper"]
    clue = world.facts["clue"]
    fix = world.facts["fix"]
    params = world.facts["params"]

    world.say(
        f"{d.label} was a {CURIOUS_TRAITS[0]} little detective who loved looking for clues "
        f"inside {world.setting.place}."
    )
    world.say(
        f"One morning, {d.label} noticed a {clue.label} near the stairs and stopped right away."
    )
    world.say(
        f"{d.label} thought the {clue.label} meant something sneaky had happened, so "
        f"{d.pronoun('subject')} hurried to tell {h.label}."
    )
    world.para()
    world.say(
        f"{h.label} listened and smiled. \"That is only a misunderstood piece from the {fix.label},\" "
        f"{h.pronoun('subject')} said."
    )
    world.say(
        f"The {fix.label} had a tiny worn spot, and the {clue.label} was just the bit that had broken off."
    )
    world.say(
        f"{d.label}'s cheeks warmed with embarrassment, but {d.pronoun('subject')} kept looking closely."
    )
    world.para()
    world.say(
        f"Then {d.label} spotted the missing place on the {fix.label} and helped {h.label} point it out."
    )
    world.say(
        f"With a short repair and a careful new fitting, the {fix.label} was safe again, and the little {clue.label} "
        f"was no longer a mystery."
    )
    world.say(
        f"{d.label} grinned at the neat fix. Curiosity had made a misunderstanding, but it also helped solve the case."
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        'Write a short detective story set in a hardware store with a stub and a banister.',
        f"Tell a child-friendly mystery where {p.name} the detective is curious about a stub and learns there was a misunderstanding.",
        "Write a simple story where a hardware-store clue turns out to be part of a banister.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    d = world.facts["detective"]
    return [
        QAItem(
            question=f"Where is the story set?",
            answer=f"The story is set in {world.setting.place}, where {d.label} looks for clues.",
        ),
        QAItem(
            question=f"What did {d.label} think the stub meant at first?",
            answer=f"{d.label} thought the stub meant something sneaky had happened, which is why {d.pronoun('subject')} hurried to tell the helper.",
        ),
        QAItem(
            question=f"What ended the misunderstanding about the stub?",
            answer=f"The helper explained that the stub was just a broken piece from the banister, so the misunderstanding was cleared up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hardware store?",
            answer="A hardware store is a shop that sells tools, building supplies, nails, screws, and other things people use to fix or build things.",
        ),
        QAItem(
            question="What is a banister?",
            answer="A banister is a handrail or railing that people can hold onto on stairs.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more, asking questions, and looking closely at things.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell(world)
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


CURATED = [
    StoryParams(name="Maya", gender="girl", helper="manager"),
    StoryParams(name="Leo", gender="boy", helper="worker"),
    StoryParams(name="Iris", gender="girl", helper="cashier"),
]


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
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
