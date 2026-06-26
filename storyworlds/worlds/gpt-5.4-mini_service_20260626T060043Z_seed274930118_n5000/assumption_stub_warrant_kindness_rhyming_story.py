#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/assumption_stub_warrant_kindness_rhyming_story.py
================================================================================================

A small storyworld for a gentle Rhyming Story about kindness, assumption,
stub, and warrant.

Premise:
- A child finds a stubby little item and makes an assumption about it.
- A warrant note reveals it belongs to someone else.
- Kindness turns the mistake into a helpful return and a warm ending.

The prose is authored as a short rhyming tale, while the world model tracks
state changes that drive the turn and resolution.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    given_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the little library"
    detail: str = "quiet shelves and a sunny front step"


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, line: str) -> None:
        if line:
            self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines).strip()


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "library": Setting(place="the little library", detail="quiet shelves and a sunny front step"),
    "garden": Setting(place="the kindness garden", detail="soft dirt paths and bright flower beds"),
    "market": Setting(place="the tiny market", detail="baskets, bells, and a warm wooden counter"),
}

CHILD_NAMES = ["Mina", "Noah", "Lila", "Eli", "Ava", "Theo"]
HELPER_NAMES = ["Marta", "Owen", "Sage", "Nina", "Iris", "Leo"]


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    risk_word: str
    value_word: str
    owner_role: str
    requires_kindness: bool = True


THING = Thing(
    id="stub",
    label="stub",
    phrase="a little paper stub",
    risk_word="small and lonely",
    value_word="important",
    owner_role="librarian",
)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _rhyming_wrap(text: str) -> str:
    return text.strip()


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    stub = world.add(Entity(id="stub", type="thing", label=THING.label, phrase=THING.phrase, owner="librarian"))

    child.memes["curiosity"] = 1
    child.memes["kindness"] = 0
    child.memes["assumption"] = 1
    child.memes["worry"] = 0
    helper.memes["kindness"] = 1

    world.say(
        f"At {setting.place}, with {setting.detail}, lived {child.id} in a bright, soft gleam."
    )
    world.say(
        f"{child.id} found {THING.phrase}, a stub so small, and made an assumption in a dream."
    )
    world.say(
        f"{child.id} thought, 'It looks like trash,' and tucked it near, but that was not the right seam."
    )

    # Conflict turn: the child notices a warrant note.
    child.memes["worry"] += 1
    world.say(
        f"Then came a tiny warrant note: 'Please return the stub; it belongs to someone keen.'"
    )
    world.say(
        f"{child.id} blinked and frowned, 'Oh no,' they said, 'my guess was wrong and not quite clean.'"
    )

    # Kindness turn.
    child.memes["kindness"] += 1
    child.memes["assumption"] = 0
    world.say(
        f"{child.id} did a kind little thing and took the stub back, careful and serene."
    )
    world.say(
        f"At the desk, {child.id} gave it back and said, 'I'm sorry; I want to help the scene.'"
    )
    world.say(
        f"The helper smiled, and the room grew warm; a thank-you sparkled bright and green."
    )
    world.say(
        f"With kindness shared, the stub was home, and {child.id} walked out light, neat, and clean."
    )

    world.facts.update(
        child=child,
        helper=helper,
        stub=stub,
        setting=setting,
        assumption_made=True,
        assumption_correct=False,
        warrant_seen=True,
        kindness_shown=True,
        returned=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Rhyming Story for a young child about kindness, an assumption, a stub, and a warrant at {f["setting"].place}.',
        f"Tell a gentle story where {f['child'].id} finds a stub, makes the wrong assumption, and then uses kindness to make it right.",
        f'Write a simple rhyming tale that includes the words "assumption", "stub", and "warrant" and ends with a kind return.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {child.id} find the stub?",
            answer=f"{child.id} found the stub at {setting.place}, where the shelves and steps were quiet and bright.",
        ),
        QAItem(
            question=f"What wrong assumption did {child.id} make about the stub?",
            answer=f"{child.id} first assumed the stub was trash, but that guess was wrong.",
        ),
        QAItem(
            question=f"What did the warrant note ask {child.id} to do?",
            answer=f"The warrant note asked {child.id} to return the stub to its owner.",
        ),
        QAItem(
            question=f"How did {child.id} fix the mistake?",
            answer=f"{child.id} showed kindness, carried the stub back carefully, and returned it with an apology.",
        ),
        QAItem(
            question=f"How did the helper respond at the end?",
            answer=f"{helper.id} smiled, thanked {child.id}, and helped the room feel warm and calm again.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is kindness?",
        answer="Kindness is when you choose to be gentle, helpful, and caring toward someone else.",
    ),
    QAItem(
        question="What is a warrant?",
        answer="In this story, a warrant is a note that says something should be returned to the right person.",
    ),
    QAItem(
        question="What is a stub?",
        answer="A stub is a small leftover piece, like a tiny bit of paper, pencil, or ticket.",
    ),
    QAItem(
        question="What is an assumption?",
        answer="An assumption is a guess you make before you know all the facts.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/3.

place(library).
place(garden).
place(market).

kindness_topic(k).

assumption_wrong(A) :- child(A), sees_stub(A), sees_warrant(A).
valid_story(P, C, H) :- place(P), child(C), helper(H).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for name in CHILD_NAMES:
        lines.append(asp.fact("child", name))
    for name in HELPER_NAMES:
        lines.append(asp.fact("helper", name))
    lines.append(asp.fact("topic", "kindness"))
    lines.append(asp.fact("thing", THING.id))
    lines.append(asp.fact("requires_kindness", THING.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as err:  # pragma: no cover
        print(f"Unable to import clingo helper: {err}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    py = sorted((p, c, h) for p in SETTINGS for c in CHILD_NAMES for h in HELPER_NAMES)
    if atoms == py:
        print(f"OK: ASP parity holds for {len(py)} simple story triples.")
        return 0
    print("MISMATCH between ASP and Python story triples.")
    if set(atoms) - set(py):
        print("  only in ASP:", sorted(set(atoms) - set(py)))
    if set(py) - set(atoms):
        print("  only in Python:", sorted(set(py) - set(atoms)))
    return 1


# ---------------------------------------------------------------------------
# Generation / validation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small Rhyming Story world about kindness, assumption, stub, and warrant.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    child_name = args.name or rng.choice(CHILD_NAMES)
    helper_name = args.helper or rng.choice([n for n in HELPER_NAMES if n != child_name])
    if helper_name == child_name:
        raise StoryError("The helper should be a different person from the child.")
    return StoryParams(
        place=place,
        child_name=child_name,
        child_type="girl" if child_name in {"Mina", "Lila", "Ava"} else "boy",
        helper_name=helper_name,
        helper_type="girl" if helper_name in {"Marta", "Nina", "Iris", "Sage"} else "boy",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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
    if qa:
        print()
        print(format_qa(sample))
    if trace and sample.world is not None:
        print()
        print("--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")


CURATED = [
    StoryParams(place="library", child_name="Mina", child_type="girl", helper_name="Owen", helper_type="boy"),
    StoryParams(place="garden", child_name="Theo", child_type="boy", helper_name="Marta", helper_type="girl"),
    StoryParams(place="market", child_name="Ava", child_type="girl", helper_name="Leo", helper_type="boy"),
]


def asp_list() -> None:
    try:
        import storyworlds.asp as asp
    except Exception as err:
        raise SystemExit(str(err))
    model = asp.one_model(asp_program("#show valid_story/3."))
    triples = sorted(set(asp.atoms(model, "valid_story")))
    print(f"{len(triples)} compatible triples:")
    for t in triples:
        print("  ", t)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
