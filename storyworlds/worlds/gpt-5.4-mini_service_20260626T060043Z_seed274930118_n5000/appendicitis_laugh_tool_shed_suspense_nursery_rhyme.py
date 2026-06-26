#!/usr/bin/env python3
"""
appendicitis_laugh_tool_shed_suspense_nursery_rhyme.py
======================================================

A small, self-contained story world about a child in a tool shed, a worried
belly, and a suspenseful turn that ends in safety and comfort.

The world is built to stay close to a nursery-rhyme cadence: short lines,
simple concrete images, and a gentle ending. The central tension is that the
child wants to laugh and play in the tool shed, but a tummy pain grows into a
serious problem that the grown-up notices in time.
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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"pain": 0.0, "dust": 0.0, "care": 0.0, "worry": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "suspense": 0.0, "comfort": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the tool shed"
    indoors: bool = True


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    name: str = "Nell"
    gender: str = "girl"
    parent: str = "mother"
    seed: Optional[int] = None


NAMES = {
    "girl": ["Nell", "Mia", "June", "Luna", "Pip"],
    "boy": ["Finn", "Toby", "Theo", "Noah", "Max"],
}
PARENTS = ["mother", "father"]
TRAITS = ["tiny", "brave", "curious", "gentle", "cheery"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A child is in suspense when belly pain grows and a grown-up has not yet
% understood what is wrong.
in_suspense(C) :- pain(C,P), P >= 1, waiting_for_help(C).

% A serious belly concern is suspected when pain is high and the child
% cannot settle even after laughing.
needs_help(C) :- pain(C,P), P >= 2, laughter(C,L), L >= 1.

% A story is valid when the setting is the tool shed and the ending reaches
% comfort.
valid_story(tool_shed) :- place(tool_shed), comfort_reached.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "tool_shed"),
        asp.fact("setting_kind", "tool_shed", "shed"),
        asp.fact("style", "nursery_rhyme"),
        asp.fact("feature", "suspense"),
        asp.fact("keyword", "appendicitis"),
        asp.fact("keyword", "laugh"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_ok = bool(asp.atoms(model, "valid_story"))
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH between ASP and Python story gate.")
        return 1
    print("OK: ASP and Python gates agree.")
    return 0


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _grow_pain(world: World, child: Entity) -> None:
    child.meters["pain"] += 1.0
    child.memes["suspense"] += 1.0
    child.memes["fear"] += 0.5


def _notice(world: World, parent: Entity, child: Entity) -> None:
    parent.memes["worry"] += 1.0
    world.say(
        f"{parent.pronoun().capitalize()} noticed {child.pronoun('possessive')} face grow pale."
    )
    world.say(
        f'"Something hurts in your belly," {parent.pronoun("subject")} said, '
        f"soft and low."
    )


def _reveal(world: World, child: Entity) -> None:
    child.memes["suspense"] += 1.0
    world.say(
        f"{child.pronoun().capitalize()} tried to laugh, but the laugh came thin."
    )
    world.say(
        f"Then came a word as sharp as a pin: appendicitis."
    )


def _help(world: World, parent: Entity, child: Entity) -> None:
    child.meters["care"] += 1.0
    child.memes["comfort"] += 1.0
    parent.memes["comfort"] += 1.0
    world.say(
        f"{parent.pronoun().capitalize()} gathered {child.pronoun('object')} up in a hurry."
    )
    world.say(
        f"They left the tool shed, and the tools stayed still."
    )
    world.say(
        f"At the clinic, a doctor helped at once, and the scary pain grew small and still."
    )
    child.meters["pain"] = 0.0
    child.memes["suspense"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["joy"] += 1.0
    world.facts["comfort_reached"] = True


def tell_story(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"In the little tool shed, beneath a tin roof low, "
        f"{child.id} found a hammer and a wooden row."
    )
    world.say(
        f"{child.id} wanted to laugh and tap-tap-tap, "
        f"but a tiny belly pain began to snap."
    )
    _grow_pain(world, child)
    world.para()
    world.say(
        f"The shed was quiet. The old rake stood near. "
        f"{child.id} held still and felt the sting of fear."
    )
    _grow_pain(world, child)
    _notice(world, parent, child)
    world.say(
        f"{child.id} whispered, \"I can laugh, but I cannot play.\""
    )
    _reveal(world, child)
    world.para()
    _help(world, parent, child)
    world.say(
        f"So now the tool shed is just where the story began, "
        f"but {child.id} is safe, with a kinder plan."
    )
    world.say(
        f"And when {child.id} laughs, it is warm and bright, "
        f"like a lantern shining through the night."
    )


def build_world(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    world.facts.update(
        child=child,
        parent=parent,
        comfort_reached=False,
        place="tool_shed",
        style="nursery_rhyme",
        feature="suspense",
    )
    tell_story(world, child, parent)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    return [
        'Write a short nursery-rhyme-like story set in a tool shed with a suspenseful belly-pain scare.',
        f"Tell a gentle story where {child.id} wants to laugh in the tool shed, but {parent.pronoun('possessive')} parent notices a serious problem.",
        "Use simple, rhythmic sentences and end with safety, care, and a changed feeling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    return [
        QAItem(
            question=f"Where does {child.id} first start playing in the story?",
            answer="The story begins in the tool shed, where the child finds tools and tries to play.",
        ),
        QAItem(
            question=f"What feeling grows when {child.id} tries to laugh but feels wrong?",
            answer="Suspense grows, because the belly pain gets more serious and nobody knows yet how bad it is.",
        ),
        QAItem(
            question=f"What word does the parent learn when the child gets worse?",
            answer="The parent learns the word appendicitis, which names the serious belly problem.",
        ),
        QAItem(
            question=f"How does the story end for {child.id}?",
            answer="The child gets help, the pain settles down, and the ending is safe and comforting.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tool shed?",
            answer="A tool shed is a small building or room where tools are kept.",
        ),
        QAItem(
            question="What does laugh mean?",
            answer="To laugh means to make happy, bouncy sounds because something feels funny or joyful.",
        ),
        QAItem(
            question="What is appendicitis?",
            answer="Appendicitis is a serious illness where the appendix becomes swollen and causes belly pain.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next when something is uncertain or worrying.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if n:
            bits.append(f"memes={n}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny story world in a tool shed with appendicitis, laugh, suspense, and a nursery-rhyme style."
    )
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Nell", gender="girl", parent="mother"),
            StoryParams(name="Finn", gender="boy", parent="father"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
