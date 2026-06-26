#!/usr/bin/env python3
"""
A small standalone storyworld: a vole, a psychology-ist, and a question at a
construction site, told with a Space Adventure feel and a transformation-dialogue
turn.

The world is intentionally tiny and constraint-checked:
- a curious vole wants to ask a brave question,
- a psychology-ist notices worry and offers a transformation into safer gear,
- dialogue carries the turn, and
- the ending image proves the change.
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
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        if self.type in {"vole"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        if self.type in {"psychology-ist"}:
            mapping = {"subject": "they", "object": "them", "possessive": "their"}
        return mapping[case]


@dataclass
class Setting:
    place: str = "the construction site"
    afford: set[str] = field(default_factory=lambda: {"question", "transformation"})


@dataclass
class StoryParams:
    name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
SETTING = Setting()

TRANSFORMATIONS = {
    "vest": {
        "label": "a bright reflective vest",
        "effect": "safer",
        "tail": "the vest shone like a tiny star under the work lights",
    },
    "helmet": {
        "label": "a smooth safety helmet",
        "effect": "braver",
        "tail": "the helmet made her look ready for a moonwalk on the beams",
    },
    "boots": {
        "label": "sturdy work boots",
        "effect": "steadier",
        "tail": "the boots thumped softly on the planks like a slow drum",
    },
}

QUESTION_TOPICS = {
    "bridge": "How do people build a bridge without letting it wobble?",
    "tunnel": "Why does a tunnel need careful support underground?",
    "crane": "How can a crane lift heavy things so high?",
}

VOLE_NAMES = ["Pip", "Moss", "Tansy", "Nib", "Lumi"]
PSYCHOLOGY_IST_NAMES = ["Dr. Orbit", "Mira", "Aster", "Quill"]
TRAITS = ["curious", "small", "brave", "gentle"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _setup_story(world: World, vole: Entity, helper: Entity, question: str) -> None:
    world.say(
        f"At {world.setting.place}, little {vole.id} listened to the roar of distant "
        f"machines and the whirr of a crane against the sky."
    )
    world.say(
        f"{vole.id} was a curious vole who loved stars, tunnels, and big questions, "
        f"but today {vole.pronoun()} felt tiny beside the steel beams."
    )
    world.say(
        f"There, {helper.id} the psychology-ist checked the site map and said, "
        f'"Hello, little traveler. What question is circling in your head?"'
    )
    world.say(
        f'{vole.id} looked up and asked, "{question}"'
    )
    world.facts["question"] = question


def _tension(world: World, vole: Entity, helper: Entity, transform_key: str) -> None:
    config = TRANSFORMATIONS[transform_key]
    vole.memes["worry"] = vole.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{helper.id} smiled. \"That is a good question,\" {helper.pronoun()} said. "
        f"\"But this place is busy and bright. Let's transform you into something ready "
        f"for the site.\""
    )
    world.say(
        f"{vole.id} blinked. The words felt like a launch countdown."
    )
    world.say(
        f"{helper.id} held out {config['label']} and helped {vole.id} climb inside it."
    )
    vole.meters["transformed"] = vole.meters.get("transformed", 0.0) + 1.0
    vole.memes["confidence"] = vole.memes.get("confidence", 0.0) + 1.0
    world.facts["transformation"] = config["label"]
    world.facts["transform_key"] = transform_key


def _resolution(world: World, vole: Entity, helper: Entity) -> None:
    config = TRANSFORMATIONS[world.facts["transform_key"]]
    question = world.facts["question"]
    world.say(
        f"When the last strap clicked into place, {vole.id} felt {config['effect']}. "
        f"{config['tail']}."
    )
    world.say(
        f"Now {vole.id} could stand near the chalk marks and ask again, "
        f'"{question}"'
    )
    world.say(
        f'{helper.id} answered with a calm little smile, and together they watched '
        f'the construction site glow gold in the work lights.'
    )
    world.say(
        f"At the end, {vole.id} was still a vole, but now {vole.pronoun()} wore the "
        f"{config['label']} and looked like a tiny astronaut helping on Earth."
    )


def tell_story(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    world = World(SETTING)
    vole = world.add(Entity(
        id=params.name,
        kind="character",
        type="vole",
        traits=["small", rng.choice(TRAITS)],
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="psychology-ist",
        traits=["calm", "helpful"],
    ))

    question = rng.choice(list(QUESTION_TOPICS.values()))
    transform_key = rng.choice(list(TRANSFORMATIONS.keys()))

    _setup_story(world, vole, helper, question)
    world.para()
    _tension(world, vole, helper, transform_key)
    world.para()
    _resolution(world, vole, helper)
    world.facts.update(
        vole=vole,
        helper=helper,
        setting=world.setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short Space Adventure-style story about a vole at a construction site.',
        f"Tell a gentle story where a psychology-ist helps a vole ask a question safely.",
        "Write a child-friendly story with dialogue and a transformation into safety gear.",
    ]


def story_qa(world: World) -> list[QAItem]:
    vole: Entity = world.facts["vole"]
    helper: Entity = world.facts["helper"]
    question: str = world.facts["question"]
    transform: str = world.facts["transformation"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {vole.id}, a curious little vole, and {helper.id}, a psychology-ist at the construction site.",
        ),
        QAItem(
            question=f"What did {vole.id} ask?",
            answer=f"{vole.id} asked, \"{question}\"",
        ),
        QAItem(
            question=f"What helped {vole.id} feel braver?",
            answer=f"{helper.id} helped by transforming {vole.id} into {transform}, which made the vole feel ready for the site.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a construction site?",
            answer="A construction site is a place where people build or repair things like buildings, roads, and bridges.",
        ),
        QAItem(
            question="What is a psychology-ist in this world?",
            answer="A psychology-ist is a calm helper who listens to feelings and helps someone think clearly about a hard moment.",
        ),
        QAItem(
            question="What is a transformation in a story like this?",
            answer="A transformation is when someone changes into a helpful new form or outfit so they can face the moment more safely.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A vole is curious when it asks a question at the construction site.
curious(vole) :- question_at_site.

% A helpful transformation is reasonable when a psychology-ist listens first.
reasonable_transformation(vest) :- psychology_ist_listens.
reasonable_transformation(helmet) :- psychology_ist_listens.
reasonable_transformation(boots) :- psychology_ist_listens.

% A full story requires: vole, psychology-ist, question, transformation, dialogue.
valid_story :- vole_present, psychology_ist_present, question_present, dialogue_present, transformation_present.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("vole_present"),
        asp.fact("psychology_ist_present"),
        asp.fact("question_present"),
        asp.fact("dialogue_present"),
        asp.fact("transformation_present"),
        asp.fact("question_at_site"),
        asp.fact("psychology_ist_listens"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/0. #show reasonable_transformation/1."))
    shown = {str(atom) for atom in model}
    expected = {"valid_story", "reasonable_transformation(vest)", "reasonable_transformation(helmet)", "reasonable_transformation(boots)"}
    if shown == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("  ASP:", sorted(shown))
    print("  PY :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A vole, a psychology-ist, and a question at a construction site."
    )
    ap.add_argument("--name", choices=VOLE_NAMES)
    ap.add_argument("--helper-name", choices=PSYCHOLOGY_IST_NAMES)
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
    return StoryParams(
        name=args.name or rng.choice(VOLE_NAMES),
        helper_name=args.helper_name or rng.choice(PSYCHOLOGY_IST_NAMES),
        seed=args.seed,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    for k, v in world.facts.items():
        if k in {"vole", "helper", "setting"}:
            continue
        lines.append(f"  fact {k}: {v}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
    StoryParams(name="Pip", helper_name="Dr. Orbit", seed=1),
    StoryParams(name="Moss", helper_name="Mira", seed=2),
    StoryParams(name="Lumi", helper_name="Quill", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0. #show reasonable_transformation/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} with {p.helper_name}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
