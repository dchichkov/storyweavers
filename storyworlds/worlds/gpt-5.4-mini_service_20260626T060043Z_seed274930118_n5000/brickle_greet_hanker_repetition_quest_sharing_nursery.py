#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a child who hankers for a brickle treat,
greets friends, and learns sharing through a small quest.

The world is built around:
- repetition as a soothing refrain,
- a quest for a brickle,
- sharing as the resolution,
- child-facing, gentle nursery-rhyme style.
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
# Domain constants
# ---------------------------------------------------------------------------

LOCATIONS = {
    "nursery": "the nursery",
    "garden": "the little garden",
    "hill": "the sunny hill",
    "kitchen": "the cozy kitchen",
}

CHARACTER_NAMES = [
    "Mina", "Toby", "Lulu", "Pip", "Nora", "Dilly", "Sia", "Wren"
]

HELPER_NAMES = [
    "Mum", "Dad", "Auntie", "Grandma", "Brother", "Sister"
]

TREATS = {
    "brickle": {
        "name": "brickle",
        "phrase": "a crumbly brickle",
        "texture": "sweet and brittle",
        "sharing_size": 3,
    },
}

# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    shares_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    name: str
    helper: str
    treat: str = "brickle"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A treat is shareable when there are at least two mouths to pass it to.
shareable(T) :- treat(T), portions(T,N), N >= 2.

% A story is reasonable when the hero hankers for a treat, has a quest,
% and the ending resolves through sharing.
reasonable_story(P, N, H, T) :- place(P), child(N), helper(H), treat(T),
    hanker(N, T), quest(T), shareable(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in LOCATIONS:
        lines.append(asp.fact("place", pid))
    for name in CHARACTER_NAMES:
        lines.append(asp.fact("child", name))
    for helper in HELPER_NAMES:
        lines.append(asp.fact("helper", helper))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("quest", tid))
        lines.append(asp.fact("portions", tid, t["sharing_size"]))
        lines.append(asp.fact("hanker", "anychild", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/4."))
    return sorted(set(asp.atoms(model, "reasonable_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_reasonable())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in LOCATIONS:
        for name in CHARACTER_NAMES:
            for helper in HELPER_NAMES:
                combos.append((place, name, helper, "brickle"))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(LOCATIONS))
    name = args.name or rng.choice(CHARACTER_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    if args.treat and args.treat not in TREATS:
        raise StoryError("Unknown treat; only brickle is supported in this world.")
    if args.name and args.helper and args.name == args.helper:
        raise StoryError("The child and helper must be different characters.")
    return StoryParams(place=place, name=name, helper=helper, treat=args.treat or "brickle")


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(place=LOCATIONS[params.place])
    child = world.add(Entity(id=params.name, kind="character", label=params.name))
    helper = world.add(Entity(id=params.helper, kind="character", label=params.helper))
    treat = world.add(Entity(
        id=params.treat,
        kind="thing",
        label="brickle",
        phrase="a crumbly brickle",
        owner=helper.id,
    ))

    child.memes["hanker"] = 1.0
    child.memes["joy"] = 0.0
    child.memes["sharing"] = 0.0
    helper.memes["kindness"] = 1.0
    treat.meters["sweet"] = 1.0

    world.facts.update(child=child, helper=helper, treat=treat, params=params)
    return world


def tell(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    treat: Entity = f["treat"]
    place = world.place

    world.say(f"At {place}, {child.id} was a little child with a soft, keen stare.")
    world.say(f"{child.id} would greet the day and greet the sun, and then {child.id} would hanker for {treat.label}.")
    world.say(f"\"Brickle, brickle,\" sang {child.id}, \"give me a crumb of brickle.\"")

    world.para()
    world.say(f"{child.id} went on a small quest across {place}, step by step and breeze by breeze.")
    world.say(f"{child.id} looked under a leaf, and under a bench, and under a bright blue bowl.")
    world.say(f"At last, {helper.id} smiled and held up the {treat.phrase}.")

    world.para()
    world.say(f"\"Greet me first,\" said {helper.id}, with a warm and merry grin.")
    world.say(f"So {child.id} said, \"Hello, hello,\" and the words went soft as a feather.")
    world.say(f"{child.id} did not gobble the brickle.")
    world.say(f"{child.id} shared the brickle with {helper.id}, and then with a tiny friend nearby.")
    world.say(f"Nibble by nibble, the brickle was gone, and {child.id}'s hankering turned into happy humming.")
    world.say(f"At the end, {child.id} was smiling, {helper.id} was smiling, and the shared crumbs sparkled like stars.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    return [
        f"Write a nursery-rhyme story about {child.id} who hankers for brickle, greets a helper, and learns to share.",
        f"Tell a gentle little quest where {child.id} goes looking for brickle with {helper.id} and everyone ends by sharing.",
        f"Create a short rhyme in which a child says greet, hanker, and brickle, then finds a happy sharing ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"What did {child.id} hanker for at {world.place}?",
            answer=f"{child.id} hankered for brickle, a crumbly treat, and kept looking for it on the little quest.",
        ),
        QAItem(
            question=f"Who helped {child.id} find the brickle?",
            answer=f"{helper.id} helped {child.id} find the brickle and reminded {child.id} to greet first.",
        ),
        QAItem(
            question=f"What did {child.id} do at the end with the brickle?",
            answer=f"{child.id} shared the brickle, so the treat became a happy thing for everyone nearby.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share something?",
            answer="To share means to let another person enjoy some of it too, instead of keeping it all.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a small mission or search for something important.",
        ),
        QAItem(
            question="Why do people greet each other?",
            answer="People greet each other to say hello and be friendly.",
        ),
        QAItem(
            question="What makes a nursery rhyme feel sing-song?",
            answer="A nursery rhyme often uses simple words, repeats, and a gentle rhythm that sounds nice when spoken aloud.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about brickle, greet, hanker, quest, and sharing.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--name", choices=CHARACTER_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--treat", choices=TREATS, default="brickle")
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


CURATED = [
    StoryParams(place="nursery", name="Mina", helper="Mum", treat="brickle"),
    StoryParams(place="garden", name="Pip", helper="Grandma", treat="brickle"),
    StoryParams(place="kitchen", name="Lulu", helper="Dad", treat="brickle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        model = asp_reasonable()
        print(f"{len(model)} reasonable stories:")
        for row in model:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} at {p.place} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
