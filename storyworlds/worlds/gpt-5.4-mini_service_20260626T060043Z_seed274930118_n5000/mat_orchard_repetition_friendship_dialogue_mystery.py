#!/usr/bin/env python3
"""
storyworlds/worlds/mat_orchard_repetition_friendship_dialogue_mystery.py
=======================================================================

A small story world in an orchard, built around a mat, friendship, repetition,
dialogue, and a light mystery.

Premise:
A child and a friend spread a mat under an apple tree in an orchard. A small
mystery begins when something important seems to be missing.

State-driven arc:
- The mat marks the picnic spot.
- Repetition appears as the characters search the same rows of trees in a careful pattern.
- Friendship softens the worry and keeps the search cooperative.
- Dialogue moves the story forward with clues and guesses.
- The mystery resolves when the missing thing is found near the mat.

This world intentionally stays small and classical: one domain, a few typed
entities, and a single causal turn that changes the ending image.
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
# Core model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    near: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the orchard"
    affords: set[str] = field(default_factory=lambda: {"picnic", "search"})


@dataclass
class MysteryObject:
    id: str
    label: str
    phrase: str
    type: str
    owner_kind: str = "character"


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    mystery: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
SETTING = Setting(place="the orchard")

CHILD_NAMES = ["Mia", "Noah", "Lina", "Eli", "Tara", "Owen"]
FRIEND_NAMES = ["Jun", "Rae", "Pip", "Sage", "Zuri", "Finn"]

MYSTERIES = {
    "red_ribbon": MysteryObject(
        id="red_ribbon",
        label="red ribbon",
        phrase="a little red ribbon",
        type="ribbon",
    ),
    "silver_key": MysteryObject(
        id="silver_key",
        label="silver key",
        phrase="a small silver key",
        type="key",
    ),
    "berry_basket": MysteryObject(
        id="berry_basket",
        label="basket",
        phrase="a tiny berry basket",
        type="basket",
    ),
}


# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------
def valid_story_combo(place: str, mystery: str) -> bool:
    return place == "the orchard" and mystery in MYSTERIES


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when it is set in the orchard and has a known mystery object.
valid_story(Place, Mystery) :- orchard(Place), mystery(Mystery).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("orchard", "the_orchard"))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("the_orchard", m) for m in MYSTERIES if valid_story_combo("the orchard", m)}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python gates.")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    if not valid_story_combo(params.place, params.mystery):
        raise StoryError("This world only supports orchard stories with a known mystery object.")

    world = World(SETTING)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    mat = world.add(Entity(id="mat", type="mat", label="mat", phrase="a blue picnic mat"))
    mystery = MYSTERIES[params.mystery]
    lost = world.add(Entity(id=mystery.id, type=mystery.type, label=mystery.label, phrase=mystery.phrase))

    world.facts.update(child=child, friend=friend, mat=mat, mystery=lost, params=params)
    return world


def search_pattern(world: World, child: Entity, friend: Entity) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    friend.memes["kindness"] = friend.memes.get("kindness", 0.0) + 1
    world.say(
        f"{child.id} and {friend.id} spread a mat under the apple trees in the orchard."
    )
    world.say(
        f"They looked once, then looked again. 'It's not here,' {child.id} said. "
        f"'Let's check the next row,' {friend.id} said."
    )


def lose_and_notice(world: World, child: Entity, mystery: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    world.say(
        f"On the mat sat {child.id}'s picnic things, but one thing seemed gone: {mystery.phrase}."
    )
    world.say(
        f"{child.id} stared at the grass and asked, 'Where did it go?'"
    )


def clue_talk(world: World, child: Entity, friend: Entity, mystery: Entity) -> None:
    child.memes["search"] = child.memes.get("search", 0.0) + 1
    friend.memes["search"] = friend.memes.get("search", 0.0) + 1
    world.say(
        f"'Look near the mat,' {friend.id} said. 'Maybe it slipped when we sat down.'"
    )
    world.say(
        f"{child.id} nodded. 'Near the mat... near the mat,' {child.id} repeated, "
        f"as if saying it twice might make the clue clearer."
    )


def resolve_mystery(world: World, child: Entity, friend: Entity, mystery: Entity, mat: Entity) -> None:
    mystery.near = mat.id
    world.say(
        f"They checked beside the mat, and there it was at last: {mystery.phrase}, caught in the grass."
    )
    world.say(
        f"{child.id} laughed with relief. {friend.id} smiled back, and together they packed up the mat with the found treasure."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    child = world.get(params.child_name)
    friend = world.get(params.friend_name)
    mat = world.get("mat")
    mystery = world.get(params.mystery)

    world.say(
        f"One morning, {child.id} went to {world.setting.place} with {friend.id} and a blue picnic mat."
    )
    world.say(
        f"They liked the orchard because the trees made soft shadows and the apples smelled sweet."
    )

    world.para()
    lose_and_notice(world, child, mystery)
    search_pattern(world, child, friend)

    world.para()
    clue_talk(world, child, friend, mystery)
    resolve_mystery(world, child, friend, mystery, mat)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    mystery = world.facts["mystery"]
    return [
        'Write a short mystery story for a young child in an orchard with a picnic mat.',
        f"Tell a gentle story where {p.child_name} and {p.friend_name} search for {mystery.label} near a mat.",
        "Write a simple orchard story with repetition, friendship, and dialogue that ends when the missing thing is found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    friend = world.facts["friend"]
    mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"What were {p.child_name} and {p.friend_name} doing in the orchard?",
            answer=f"They were having a picnic on a mat and then looking for {mystery.phrase}.",
        ),
        QAItem(
            question=f"What clue did {friend.id} give {child.id}?",
            answer=f"{friend.id} told {child.id} to look near the mat because the missing thing might have slipped there.",
        ),
        QAItem(
            question=f"How did the story use repetition?",
            answer=f"{child.id} repeated 'near the mat' while the two friends checked the orchard in a careful pattern.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"They found {mystery.phrase} in the grass beside the mat, and the worry turned into relief.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mat used for?",
            answer="A mat is a flat piece of cloth or material that people can sit on for a picnic or play on.",
        ),
        QAItem(
            question="Why do people search in a pattern when something is missing?",
            answer="People search in a pattern so they do not keep looking in the same place and can check the whole area carefully.",
        ),
        QAItem(
            question="Why is a friend helpful in a mystery?",
            answer="A friend can notice clues, share ideas, and make the search feel calmer and kinder.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An orchard mystery with a mat, friendship, repetition, and dialogue.")
    ap.add_argument("--place", choices=["the orchard"], default="the orchard")
    ap.add_argument("--mystery", choices=sorted(MYSTERIES), default=None)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--child-type", choices=["girl", "boy"], default="girl")
    ap.add_argument("--friend-type", choices=["girl", "boy"], default="boy")
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
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    name = args.name or rng.choice(CHILD_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != name])
    return StoryParams(
        place="the orchard",
        child_name=name,
        child_type=args.child_type,
        friend_name=friend,
        friend_type=args.friend_type,
        mystery=mystery,
    )


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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.near:
            bits.append(f"near={e.near}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for mid in sorted(MYSTERIES):
            params = StoryParams(
                place="the orchard",
                child_name=CHILD_NAMES[0],
                child_type="girl",
                friend_name=FRIEND_NAMES[0],
                friend_type="boy",
                mystery=mid,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
