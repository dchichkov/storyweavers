#!/usr/bin/env python3
"""
A standalone storyworld for a small detective-style tale about a child,
a misunderstanding, bravery, and a lesson learned.

Premise:
- A child notices a bump or lump and thinks something scary is happening.
- A gentle helper explains it is a harmless cyst.
- The child is brave enough to ask questions and learn the truth.
- The story ends with the fear replaced by understanding.

The world keeps a tiny physical/emotional model:
- meters: physical state like ache, worry-trigger, clue-found, comfort.
- memes: emotional state like fear, bravery, relief, confusion, trust.

The prose is state-driven, not template-swapped:
the story is composed from the simulated trace of the investigation.
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
# Core entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    helper_place: str
    daytime: str


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_type: str
    helper_type: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "home": Setting(place="the cozy kitchen", helper_place="the little clinic", daytime="morning"),
    "school": Setting(place="the school hallway", helper_place="the nurse's room", daytime="afternoon"),
    "park": Setting(place="the park bench", helper_place="the doctor's office", daytime="sunny afternoon"),
}

CLUES = {
    "bump": {
        "label": "a small bump",
        "phrase": "a little bump under the skin",
        "misread": "something dangerous",
        "truth": "a harmless cyst",
    },
    "lump": {
        "label": "a soft lump",
        "phrase": "a soft lump that did not want to hurt anyone",
        "misread": "a bad surprise",
        "truth": "a harmless cyst",
    },
    "swelling": {
        "label": "a tiny swelling",
        "phrase": "a tiny swelling that looked strange",
        "misread": "an angry problem",
        "truth": "a harmless cyst",
    },
}

HELPERS = {
    "doctor": ("doctor", "the doctor"),
    "nurse": ("nurse", "the nurse"),
    "parent": ("parent", "their parent"),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn", "Zoe", "Max"]
TRAITS = ["curious", "careful", "brave", "quiet", "bright", "gentle"]


# ---------------------------------------------------------------------------
# Inline prose helpers
# ---------------------------------------------------------------------------
def _place_phrase(world: World) -> str:
    return world.setting.place


def _helper_phrase(helper: Entity) -> str:
    return helper.label or helper.type


def _child_intro(world: World, child: Entity, clue: Entity) -> None:
    world.say(
        f"{child.id} noticed {clue.phrase} at {_place_phrase(world)} and frowned at the odd little shape."
    )
    world.say(
        f"{child.pronoun().capitalize()} was a {child.meters.get('trait_word', 'curious')} kid who liked solving small mysteries."
    )


def _misunderstand(world: World, child: Entity, clue: Entity) -> None:
    child.memes["fear"] = child.memes.get("fear", 0) + 1
    child.memes["confusion"] = child.memes.get("confusion", 0) + 1
    clue.meters["noticed"] = 1
    world.say(
        f"{child.id} whispered that it might be {CLUES[clue.type]['misread']}, and that thought felt very big."
    )
    world.say(
        f"{child.pronoun().capitalize()} kept staring at the spot, trying to guess what the lump meant."
    )


def _brave_question(world: World, child: Entity, helper: Entity, clue: Entity) -> None:
    child.memes["bravery"] = child.memes.get("bravery", 0) + 1
    child.meters["asked_for_help"] = 1
    world.say(
        f"Still, {child.id} was brave enough to ask {helper.label} about it."
    )
    world.say(
        f"{helper.label.capitalize()} listened closely and promised to check the clue carefully."
    )


def _explain_cyst(world: World, child: Entity, helper: Entity, clue: Entity) -> None:
    clue.meters["explained"] = 1
    child.memes["trust"] = child.memes.get("trust", 0) + 1
    child.memes["fear"] = max(0, child.memes.get("fear", 0) - 1)
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    world.say(
        f"{helper.label.capitalize()} explained that it was {CLUES[clue.type]['truth']}, and that many cysts are not dangerous."
    )
    world.say(
        f"The strange little spot was not a monster at all; it was just a body mystery with a simple name."
    )


def _lesson_learned(world: World, child: Entity, helper: Entity, clue: Entity) -> None:
    child.memes["lesson"] = child.memes.get("lesson", 0) + 1
    world.say(
        f"{child.id} learned a good lesson: it is brave to ask questions instead of guessing the worst."
    )
    world.say(
        f"After that, {child.id} felt calmer, because knowing the truth made the mystery small enough to hold."
    )
    world.say(
        f"{child.id} and {_helper_phrase(helper)} left {_place_phrase(world)} with the little cyst understood and no longer scary."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        meters={"trait_word": 1},
        memes={"fear": 0, "confusion": 0, "bravery": 0, "relief": 0, "trust": 0, "lesson": 0},
    ))
    helper_kind, helper_label = HELPERS[params.helper_type]
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_kind,
        label=helper_label,
        memes={"calm": 1},
    ))
    clue_def = CLUES[params.clue]
    clue = world.add(Entity(
        id="Clue",
        kind="thing",
        type=params.clue,
        label=clue_def["label"],
        phrase=clue_def["phrase"],
        meters={"noticed": 0, "explained": 0},
    ))

    world.facts.update(child=child, helper=helper, clue=clue, params=params)
    return world


def tell_story(world: World) -> None:
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    clue: Entity = world.facts["clue"]

    _child_intro(world, child, clue)
    world.say(
        f"At first, {child.id} worried the clue meant {CLUES[clue.type]['misread']}."
    )
    _misunderstand(world, child, clue)
    world.say(
        f"Then {child.id} took a breath and went to {world.setting.helper_place}."
    )
    _brave_question(world, child, helper, clue)
    _explain_cyst(world, child, helper, clue)
    _lesson_learned(world, child, helper, clue)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a short detective-style story for a young child about {p.child_name} and a harmless cyst.",
        f"Tell a gentle mystery story where a {p.child_type} learns not to fear a strange bump.",
        f"Write a small lesson-learned story about bravery, misunderstanding, and a body mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    clue: Entity = world.facts["clue"]
    return [
        QAItem(
            question=f"What did {child.id} first think the clue meant?",
            answer=f"{child.id} first thought it might be {CLUES[clue.type]['misread']}.",
        ),
        QAItem(
            question=f"What helped {child.id} feel brave enough to ask a question?",
            answer=f"{child.id} felt brave enough to ask {helper.label} for help.",
        ),
        QAItem(
            question=f"What was the strange little mystery really called?",
            answer=f"It was {CLUES[clue.type]['truth']}.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn at the end?",
            answer=f"{child.id} learned that it is brave to ask questions instead of guessing the worst.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cyst?",
            answer="A cyst is a little pocket or bump in the body that can be harmless and may need a grown-up or doctor to check it.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel nervous, like asking a question or telling a grown-up about a worry.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea about something and later learns the truth.",
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A clue is a misunderstanding when the child's first guess is wrong.
misunderstanding(C) :- clue(C), guessed_wrong(C).

% Bravery is present when the child asks for help.
brave(C) :- child(C), asked_help(C).

% The lesson is learned after the truth is explained.
lesson_learned(C) :- child(C), explained_truth(C).

% A valid story needs the three beats.
valid_story(C) :- misunderstanding(C), brave(C), lesson_learned(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for kid in HELPERS:
        lines.append(asp.fact("helper_kind", kid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("asked_help", "child"))
    lines.append(asp.fact("explained_truth", "child"))
    lines.append(asp.fact("guessed_wrong", "Clue"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/1.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {("child",)}
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH between ASP and Python world assumptions.")
    print(" ASP:", sorted(atoms))
    print(" PY :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Params, parser, generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style storyworld about a cyst, bravery, and a lesson learned.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=sorted(HELPERS))
    ap.add_argument("--clue", choices=sorted(CLUES))
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(sorted(HELPERS))
    clue = args.clue or rng.choice(sorted(CLUES))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    return StoryParams(
        setting=setting,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
        clue=clue,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def curated_samples() -> list[StoryParams]:
    return [
        StoryParams(setting="home", child_name="Mia", child_type="girl", helper_type="parent", clue="bump"),
        StoryParams(setting="school", child_name="Leo", child_type="boy", helper_type="nurse", clue="lump"),
        StoryParams(setting="park", child_name="Nora", child_type="girl", helper_type="doctor", clue="swelling"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        vals = asp.atoms(model, "valid_story")
        print(f"{len(vals)} valid_story atom(s):")
        for v in vals:
            print(" ", v)
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated_samples()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
