#!/usr/bin/env python3
"""
A tiny nursery-rhyme story world about a small, shared treasure, an odd request,
a twist, and a reconciliation.

Premise:
- In a soft nursery setting, one child finds a bright delight.
- Another child makes an aberrant solicit: an unusual request that breaks the
  normal sharing pattern.
- A twist reveals the request was not greedy, but meant to repair a hurt feeling.
- The children reconcile by sharing the treasure in a new, kinder way.
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
    kind: str = "thing"  # "child" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    holder: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def short(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the nursery corner"
    mood: str = "soft and bright"


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    color: str
    sparkle: str
    shareable: bool = True


@dataclass
class StoryParams:
    name_a: str
    kind_a: str
    name_b: str
    kind_b: str
    treasure: str
    twist: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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

TREASURES = {
    "bell": Treasure("bell", "little bell", "a little silver bell", "silver", "bright"),
    "kite": Treasure("kite", "paper kite", "a painted paper kite", "blue", "windy"),
    "ribbon": Treasure("ribbon", "red ribbon", "a red ribbon with a bow", "red", "shiny"),
}

NAMES = {
    "girl": ["Mina", "Luna", "Poppy", "Ada", "Nell"],
    "boy": ["Toby", "Finn", "Owen", "Milo", "Jasper"],
}

TYPES = {
    "girl": "girl",
    "boy": "boy",
}

TWISTS = {
    "lost_turn": "the other child had lost their turn",
    "stuck_memory": "the other child needed help remembering a happy rhyme",
    "broken_loop": "the other child had a sad thought that would not go away",
}

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------


def is_valid_story(treasure: Treasure, twist: str) -> bool:
    return treasure.shareable and twist in TWISTS


def explain_rejection(treasure: Treasure, twist: str) -> str:
    return (
        f"(No story: the treasure '{treasure.label}' cannot support the chosen twist "
        f"'{twist}' in a gentle sharing tale.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def nursery_opening(world: World, a: Entity, b: Entity, treasure: Entity) -> None:
    world.say(
        f"Under the soft lamp in {world.setting.place}, little {a.id} found {treasure.phrase}, "
        f"and {b.id} watched with round, quiet eyes."
    )
    world.say(
        f"It looked bright as a star and small as a button, and both children wanted to hold it near."
    )


def aberrant_solicit(world: World, a: Entity, b: Entity, treasure: Entity) -> None:
    a.memes["delight"] = a.memes.get("delight", 0.0) + 1.0
    b.memes["want"] = b.memes.get("want", 0.0) + 1.0
    world.say(
        f"Then {b.id} made an aberrant solicit: {b.pronoun().capitalize()} asked to keep the treasure first, "
        f"which was not the usual sharing way."
    )
    world.say(
        f"{a.id} blinked, because the request sounded odd and the room went still as a spoon in porridge."
    )


def twist_reveal(world: World, a: Entity, b: Entity, treasure: Entity, twist: str) -> None:
    world.say(
        f"But here came the twist: {TWISTS[twist]}. That was why {b.id} had asked so strangely."
    )
    world.say(
        f"{b.id} did not want to take and take; {b.pronoun('subject').capitalize()} wanted one little turn to help."
    )


def reconcile_and_share(world: World, a: Entity, b: Entity, treasure: Entity) -> None:
    a.shared_with.add(b.id)
    b.shared_with.add(a.id)
    treasure.holder = None
    world.say(
        f"{a.id} softened, and the two children made peace by sharing. First one held the treasure, then the other, "
        f"with careful hands and tiny smiles."
    )
    world.say(
        f"By the end, they were laughing in a tidy little rhythm, and the bright thing shone between them like a moon."
    )


def tell_story(params: StoryParams) -> World:
    world = World(SETTING)
    treasure_cfg = TREASURES[params.treasure]
    a = world.add(
        Entity(
            id=params.name_a,
            kind="child",
            type=params.kind_a,
            label=params.name_a,
            meters={"close": 1.0},
            memes={"hope": 1.0},
        )
    )
    b = world.add(
        Entity(
            id=params.name_b,
            kind="child",
            type=params.kind_b,
            label=params.name_b,
            meters={"close": 1.0},
            memes={"hope": 0.7},
        )
    )
    treasure = world.add(
        Entity(
            id=treasure_cfg.id,
            kind="thing",
            type="toy",
            label=treasure_cfg.label,
            phrase=treasure_cfg.phrase,
            owner=a.id,
            holder=a.id,
        )
    )

    nursery_opening(world, a, b, treasure)
    world.para()
    aberrant_solicit(world, a, b, treasure)
    world.para()
    twist_reveal(world, a, b, treasure, params.twist)
    world.para()
    reconcile_and_share(world, a, b, treasure)

    world.facts.update(
        a=a,
        b=b,
        treasure=treasure,
        twist=params.twist,
        setting=SETTING,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["a"]
    b = f["b"]
    treasure = f["treasure"]
    return [
        f"Write a nursery-rhyme style story about {a.id} and {b.id}, a bright {treasure.label}, and a strange request.",
        f"Tell a gentle story where {b.id} makes an aberrant solicit for {treasure.phrase}, then the children reconcile.",
        f"Write a rhyme-like tale about sharing {treasure.phrase} after a twist reveals why the request was made.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["a"]
    b = f["b"]
    treasure = f["treasure"]
    twist = f["twist"]
    return [
        QAItem(
            question=f"What did {b.id} ask for in the nursery?",
            answer=(
                f"{b.id} asked for the first turn with {treasure.phrase}. It was an odd request, but it made sense later."
            ),
        ),
        QAItem(
            question=f"What was unusual about {b.id}'s request?",
            answer=(
                f"It was an aberrant solicit because the children were expected to share in the usual way, "
                f"but {b.id} asked to keep it first."
            ),
        ),
        QAItem(
            question=f"What twist changed how the children felt?",
            answer=(
                f"The twist was that {TWISTS[twist]}. After that was clear, {a.id} understood the request was meant to help."
            ),
        ),
        QAItem(
            question=f"How did {a.id} and {b.id} end the story?",
            answer=(
                f"They ended by reconciling and sharing {treasure.phrase}, taking turns kindly until both were happy."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "sharing": (
        "What does it mean to share?",
        "To share means to let someone else use or enjoy something too, instead of keeping it all for yourself.",
    ),
    "twist": (
        "What is a twist in a story?",
        "A twist is a surprise that changes what you thought was happening.",
    ),
    "reconciliation": (
        "What is reconciliation?",
        "Reconciliation is when people stop being upset and make peace again.",
    ),
    "nursery": (
        "What is a nursery?",
        "A nursery is a soft, child-friendly place for play, rest, and gentle stories.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_treasure(T) :- treasure(T).
valid_twist(X) :- twist(X).
valid_story(T, X) :- valid_treasure(T), valid_twist(X), shareable(T).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("treasure", tid) for tid in TREASURES]
    lines += [asp.fact("shareable", tid) for tid, t in TREASURES.items() if t.shareable]
    lines += [asp.fact("twist", tid) for tid in TWISTS]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(t, x) for t in TREASURES for x in TWISTS if is_valid_story(TREASURES[t], x)}
    asp_set = set(asp_valid_pairs())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} pairs).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("Python only:", sorted(py - asp_set))
    print("ASP only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    name_a: str
    kind_a: str
    name_b: str
    kind_b: str
    treasure: str
    twist: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery rhyme storyworld with sharing, twist, and reconciliation.")
    ap.add_argument("--name-a", choices=NAMES["girl"] + NAMES["boy"])
    ap.add_argument("--name-b", choices=NAMES["girl"] + NAMES["boy"])
    ap.add_argument("--kind-a", choices=["girl", "boy"])
    ap.add_argument("--kind-b", choices=["girl", "boy"])
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--twist", choices=TWISTS)
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
    treasure = args.treasure or rng.choice(list(TREASURES))
    twist = args.twist or rng.choice(list(TWISTS))
    if not is_valid_story(TREASURES[treasure], twist):
        raise StoryError(explain_rejection(TREASURES[treasure], twist))
    kind_a = args.kind_a or rng.choice(["girl", "boy"])
    kind_b = args.kind_b or ("boy" if kind_a == "girl" else "girl")
    name_a = args.name_a or rng.choice(NAMES[kind_a])
    pool_b = [n for n in NAMES[kind_b] if n != name_a] or NAMES[kind_b]
    name_b = args.name_b or rng.choice(pool_b)
    return StoryParams(name_a=name_a, kind_a=kind_a, name_b=name_b, kind_b=kind_b, treasure=treasure, twist=twist)


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
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.holder:
            bits.append(f"holder={ent.holder}")
        if ent.shared_with:
            bits.append(f"shared_with={sorted(ent.shared_with)}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"{ent.id}: {', '.join(bits) if bits else '(bare)'}")
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
    StoryParams("Mina", "girl", "Toby", "boy", "bell", "lost_turn"),
    StoryParams("Luna", "girl", "Owen", "boy", "kite", "stuck_memory"),
    StoryParams("Poppy", "girl", "Milo", "boy", "ribbon", "broken_loop"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid story pairs:\n")
        for t, x in pairs:
            print(f"  {t:10} {x}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
