#!/usr/bin/env python3
"""
A small fable-style storyworld about a clearing, a yorkie, and a surprise.

Seed tale:
- In a quiet clearing, a tiny yorkie named Pip loved to explore.
- Pip noticed that the meadow animals were gloomy because a little picnic basket
  had gone missing before the spring gathering.
- Pip followed a trail, found the basket under a fern, and surprised everyone by
  bringing it back.
- The clearing turned bright again, and the animals learned that even a small
  helper can make a big happy change.

This script turns that premise into a compact simulation with physical meters
and emotional memes, plus a declarative ASP twin for parity checks.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"yorkie", "dog"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"rabbit", "fox", "hedgehog", "mouse", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Clearing:
    name: str = "the clearing"
    trail: str = "fern path"
    places: set[str] = field(default_factory=lambda: {"clearing", "fern", "oak", "stream"})


@dataclass
class StoryParams:
    clearing: str
    yorkie_name: str
    friend: str
    missing_item: str
    seed: Optional[int] = None


class World:
    def __init__(self, clearing: Clearing) -> None:
        self.clearing = clearing
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

        clone = World(self.clearing)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

CLEARINGS = {
    "clearing": Clearing(),
}

YORKIE_NAMES = ["Pip", "Milo", "Dot", "Toto", "Nell", "Gigi"]
FRIENDS = ["rabbit", "fox", "hedgehog", "mouse", "bird"]
MISSING_ITEMS = {
    "basket": ("a little picnic basket", "basket"),
    "lantern": ("a small lantern", "lantern"),
    "ribbon": ("a bright ribbon bundle", "ribbon"),
}

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------


def valid_combo(clearing: str, friend: str, item: str) -> bool:
    return clearing in CLEARINGS and friend in FRIENDS and item in MISSING_ITEMS


def valid_combos() -> list[tuple[str, str, str]]:
    return [(c, f, i) for c in CLEARINGS for f in FRIENDS for i in MISSING_ITEMS]


def explain_rejection() -> str:
    return "(No story: the clearing, friend, and missing thing must all be known choices.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% The story is valid if the chosen setting, friend, and item are all registered.
valid_story(C,F,I) :- clearing(C), friend(F), item(I).

% A surprise happens when the yorkie finds the missing item and returns it.
surprise(C) :- valid_story(C,_,_).

#show valid_story/3.
#show surprise/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for c in CLEARINGS:
        lines.append(asp.fact("clearing", c))
    for f in FRIENDS:
        lines.append(asp.fact("friend", f))
    for i in MISSING_ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------


def tell(clearing: Clearing, yorkie_name: str, friend: str, missing_item: str) -> World:
    world = World(clearing)
    yorkie = world.add(Entity(id=yorkie_name, kind="character", type="yorkie", label=yorkie_name))
    friend_ent = world.add(Entity(id=friend, kind="character", type=friend, label=f"the {friend}"))
    item_phrase, item_label = MISSING_ITEMS[missing_item]
    item = world.add(Entity(
        id=missing_item,
        kind="thing",
        type=missing_item,
        label=item_label,
        phrase=item_phrase,
        owner=friend_ent.id,
    ))

    # Act 1: the quiet clearing and the wish to help.
    yorkie.memes["curiosity"] = 1.0
    friend_ent.memes["worry"] = 1.0
    world.say(
        f"In {clearing.name}, a tiny yorkie named {yorkie.id} padded along the grass and sniffed the wind."
    )
    world.say(
        f"{friend_ent.label.capitalize()} sat near the path, looking sad because {item.phrase} had gone missing."
    )

    # Act 2: the trail and the search.
    world.para()
    yorkie.meters["steps"] = 1.0
    yorkie.memes["hope"] = 1.0
    world.say(
        f"{yorkie.id} noticed a soft trail by a fern and followed it with careful paws."
    )
    item.meters["hidden"] = 1.0
    world.say(
        f"Under the fern, {yorkie.id} found {item.phrase}, tucked away as if the little thing had been waiting for help."
    )

    # Act 3: the surprise and the turning of the mood.
    world.para()
    yorkie.memes["surprise"] = 1.0
    friend_ent.memes["joy"] = 1.0
    friend_ent.memes["worry"] = 0.0
    item.owner = yorkie.id
    item.meters["found"] = 1.0
    world.say(
        f"{yorkie.id} raced back and surprised everyone by placing {item.phrase} right where it belonged."
    )
    world.say(
        f"The {friend} smiled so wide that the whole clearing felt brighter, and {yorkie.id} wagged with quiet pride."
    )

    world.facts.update(
        yorkie=yorkie,
        friend=friend_ent,
        item=item,
        item_key=missing_item,
        clearing=clearing,
        surprise=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    yorkie = f["yorkie"]
    friend = f["friend"]
    item = f["item"]
    return [
        f'Write a short fable for young children about a yorkie named {yorkie.id}, a clearing, and a surprise.',
        f"Tell a gentle story in which {yorkie.id} helps {friend.label} by finding {item.phrase} in the clearing.",
        f'Write a simple animal fable that uses the word "surprise" and ends with the clearing feeling happy again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    yorkie = f["yorkie"]
    friend = f["friend"]
    item = f["item"]
    return [
        QAItem(
            question=f"Who was the tiny helper in the clearing?",
            answer=f"It was {yorkie.id}, a little yorkie who searched carefully and brought back the missing thing.",
        ),
        QAItem(
            question=f"What was missing before the happy surprise?",
            answer=f"{item.phrase} was missing, and that made {friend.label} feel gloomy until it was found.",
        ),
        QAItem(
            question=f"How did the story end for {friend.label}?",
            answer=f"{friend.label.capitalize()} smiled again after {yorkie.id} returned {item.phrase}, so the clearing felt bright and calm.",
        ),
        QAItem(
            question=f"Why was the ending called a surprise?",
            answer=f"It was a surprise because {yorkie.id} found {item.phrase} under the fern and brought it back when no one expected it.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "yorkie": [
        QAItem(
            question="What is a yorkie?",
            answer="A yorkie is a very small dog with a lively spirit and a fluffy coat.",
        )
    ],
    "clearing": [
        QAItem(
            question="What is a clearing?",
            answer="A clearing is an open sunny space in a forest or field where grass can grow.",
        )
    ],
    "surprise": [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that can make someone gasp, smile, or laugh.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *WORLD_KNOWLEDGE["yorkie"],
        *WORLD_KNOWLEDGE["clearing"],
        *WORLD_KNOWLEDGE["surprise"],
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parser / params / generation
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a clearing, a yorkie, and a surprise.")
    ap.add_argument("--clearing", choices=list(CLEARINGS))
    ap.add_argument("--yorkie-name", choices=YORKIE_NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--missing-item", choices=list(MISSING_ITEMS))
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
    if args.clearing:
        combos = [c for c in combos if c[0] == args.clearing]
    if args.friend:
        combos = [c for c in combos if c[1] == args.friend]
    if args.missing_item:
        combos = [c for c in combos if c[2] == args.missing_item]
    if not combos:
        raise StoryError(explain_rejection())

    clearing, friend, item = rng.choice(sorted(combos))
    yorkie_name = args.yorkie_name or rng.choice(YORKIE_NAMES)
    return StoryParams(
        clearing=clearing,
        yorkie_name=yorkie_name,
        friend=friend,
        missing_item=item,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(CLEARINGS[params.clearing], params.yorkie_name, params.friend, params.missing_item)
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
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(clearing="clearing", yorkie_name="Pip", friend="rabbit", missing_item="basket"),
    StoryParams(clearing="clearing", yorkie_name="Dot", friend="fox", missing_item="lantern"),
    StoryParams(clearing="clearing", yorkie_name="Milo", friend="hedgehog", missing_item="ribbon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3.\n#show surprise/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.yorkie_name}: clearing={p.clearing}, friend={p.friend}, item={p.missing_item}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
