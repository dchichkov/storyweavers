#!/usr/bin/env python3
"""
A small fable-style storyworld set in a bedroom.

Premise:
A curious child finds a shuttle-shaped toy and a ruminant plush in a bedroom.
The child wants to draw with a bright marker, but curiosity makes the child
reach for things that belong to others. Foreshadowing warns that taking without
asking will cause a small tangle. Sharing resolves the trouble.

This world keeps one tiny simulation:
- objects have meters (physical state) and memes (emotional state)
- the child can draw, which may leave marks
- the child can take, return, ask, and share
- the ending proves the change in state

The story is authored in a fable tone: concrete, gentle, and lesson-shaped.
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
# Story model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carries: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("marks", 0.0)
        self.meters.setdefault("touched", 0.0)
        self.meters.setdefault("moved", 0.0)
        self.meters.setdefault("clean", 1.0)
        self.memes.setdefault("curiosity", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("sharing", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Bedroom:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=lambda: {"draw", "share", "look"})


@dataclass
class World:
    setting: Bedroom
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------

@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    kind: str
    leaves_marks: bool = False


@dataclass
class Companion:
    id: str
    label: str
    phrase: str
    kind: str


TOOLS = {
    "marker": Tool(
        id="marker",
        label="marker",
        phrase="a bright red marker",
        kind="ink",
        leaves_marks=True,
    ),
    "pencil": Tool(
        id="pencil",
        label="pencil",
        phrase="a short blue pencil",
        kind="graphite",
        leaves_marks=False,
    ),
}

SHARED_ITEMS = {
    "shuttle": Entity(
        id="shuttle",
        kind="thing",
        type="toy",
        label="shuttle toy",
        phrase="a small shuttle-shaped toy",
        owner="parent",
        plural=False,
    ),
    "ruminant": Entity(
        id="ruminant",
        kind="thing",
        type="plush",
        label="ruminant plush",
        phrase="a soft ruminant plush with kind eyes",
        owner="parent",
        plural=False,
    ),
}

CURIOUS_KIDS = ["Mina", "Leo", "Nora", "Finn", "Ivy", "Theo"]
TRAITS = ["curious", "gentle", "bright", "careful"]


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% The story is valid when the child is curious, the bedroom has a tool,
% the child can draw, and sharing can resolve the worry around borrowed things.
valid_story(N) :- child(N), curious(N), has_tool(marker), has_item(shuttle), has_item(ruminant).
foreshadowing(N) :- valid_story(N), sees_hint(N).
shared_end(N) :- valid_story(N), asks_first(N), returns_item(N), shares_time(N).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "bedroom"), asp.fact("has_tool", "marker"), asp.fact("has_item", "shuttle"), asp.fact("has_item", "ruminant")]
    for n in CURIOUS_KIDS:
        lines.append(asp.fact("child", n))
        lines.append(asp.fact("curious", n))
        lines.append(asp.fact("asks_first", n))
        lines.append(asp.fact("returns_item", n))
        lines.append(asp.fact("shares_time", n))
        lines.append(asp.fact("sees_hint", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_children() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((name,) for name in CURIOUS_KIDS)
    cl = set(asp_valid_children())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} children).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------

def _do_draw(world: World, child: Entity, tool: Entity) -> None:
    child.memes["curiosity"] += 1
    if tool.id == "marker":
        tool.meters["marks"] += 1
        child.meters["marks"] += 1
    else:
        child.meters["marks"] += 0.2
    world.say(
        f"{child.id} drew a little picture with {tool.phrase}, and the page began to look like a tiny sky."
    )


def _foreshadow(world: World, child: Entity) -> None:
    child.memes["worry"] += 1
    world.say(
        f"Near the bed, the shuttle toy and the ruminant plush sat side by side, as if they were waiting for a choice."
    )
    world.say(
        f"{child.id} noticed that taking one without asking would not feel fair."
    )


def _take_without_asking(world: World, child: Entity, item: Entity) -> None:
    child.memes["curiosity"] += 1
    child.meters["touched"] += 1
    item.meters["moved"] += 1
    world.say(f"{child.id} reached for the {item.label} before asking.")


def _ask_and_share(world: World, child: Entity, item: Entity) -> None:
    child.memes["sharing"] += 1
    child.memes["joy"] += 1
    item.owner = child.id
    world.say(
        f"{child.id} paused, asked first, and then shared the {item.label} with a smile."
    )


def _resolve(world: World, child: Entity, shuttle: Entity, ruminant: Entity) -> None:
    child.memes["worry"] = 0.0
    child.memes["joy"] += 1
    world.say(
        f"In the end, {child.id} gave back the shuttle toy, left the ruminant plush safe on the quilt, and felt lighter for it."
    )
    world.say(
        f"The bedroom stayed tidy, the drawing stayed bright, and the little lesson was easy to remember."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------

def tell(name: str = "Mina", trait: str = "curious", parent: str = "mother") -> World:
    world = World(setting=Bedroom())
    child = world.add(Entity(
        id=name, kind="character", type="girl" if name in {"Mina", "Nora", "Ivy"} else "boy",
        label=name, phrase=f"a {trait} child named {name}",
    ))
    parent_ent = world.add(Entity(
        id="parent", kind="character", type=parent, label=parent, phrase=f"the {parent}",
    ))
    marker = world.add(Entity(
        id="marker", kind="thing", type="tool", label="marker", phrase=TOOLS["marker"].phrase
    ))
    shuttle = world.add(Entity(**{**SHARED_ITEMS["shuttle"].__dict__}))
    ruminant = world.add(Entity(**{**SHARED_ITEMS["ruminant"].__dict__}))

    world.say(
        f"In the bedroom, {child.id} was a {trait} little child who loved to look closely at every bright thing."
    )
    world.say(
        f"{child.id} found {marker.phrase} beside a picture book and wanted to draw at once."
    )
    world.say(
        f"{child.id} also noticed a shuttle toy and a ruminant plush on the bed, and that made the room feel like a secret waiting to be understood."
    )

    world.para()
    _foreshadow(world, child)
    _take_without_asking(world, child, shuttle)
    world.say(
        f"{parent_ent.label.capitalize()} gave a calm look, because even small borrowing can turn a kind room into a worried one."
    )

    world.para()
    _do_draw(world, child, marker)
    _ask_and_share(world, child, ruminant)
    _resolve(world, child, shuttle, ruminant)

    world.facts.update(
        child=child,
        parent=parent_ent,
        marker=marker,
        shuttle=shuttle,
        ruminant=ruminant,
        setting=world.setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        'Write a short fable for a young child in a bedroom about curiosity, foreshadowing, and sharing.',
        f"Tell a gentle story where {child.id} wants to draw, notices a shuttle toy and a ruminant plush, and learns to ask first.",
        "Write a bedroom story that ends with a child sharing instead of taking without asking.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    return [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens in the bedroom, where {child.id} can see the bed, the picture book, and the toys all at once.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with the marker?",
            answer=f"{child.id} wanted to draw a little picture, because curiosity made the marker feel exciting.",
        ),
        QAItem(
            question=f"Which two toys made the choice feel important?",
            answer="The shuttle toy and the ruminant plush made the choice matter, because they were things the child should ask about first.",
        ),
        QAItem(
            question=f"How did the story show foreshadowing?",
            answer=f"It showed foreshadowing when {child.id} noticed the toys waiting on the bed and felt that taking without asking would not be fair.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} giving back the shuttle toy, sharing the ruminant plush, and feeling lighter because the bedroom stayed tidy and kind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shuttle toy?",
            answer="A shuttle toy is a toy shaped like a spacecraft that people can hold, move, and imagine flying through space.",
        ),
        QAItem(
            question="What is a ruminant?",
            answer="A ruminant is an animal that chews its food again after swallowing it, like a cow, sheep, or goat.",
        ),
        QAItem(
            question="Why should children ask before taking a toy?",
            answer="Children should ask before taking a toy because asking shows respect for other people's things and helps everyone stay calm.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use, enjoy, or hold something too, so the good thing can be part of both people's time.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    name: str = "Mina"
    trait: str = "curious"
    parent: str = "mother"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable-style bedroom storyworld.")
    ap.add_argument("--name", choices=CURIOUS_KIDS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--parent", choices=["mother", "father"])
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
    name = args.name or rng.choice(CURIOUS_KIDS)
    trait = args.trait or rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(name=name, trait=trait, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(name=params.name, trait=params.trait, parent=params.parent)
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


# ---------------------------------------------------------------------------
# ASP utilities
# ---------------------------------------------------------------------------

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mina", trait="curious", parent="mother"),
            StoryParams(name="Leo", trait="careful", parent="father"),
            StoryParams(name="Nora", trait="gentle", parent="mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
