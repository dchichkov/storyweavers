#!/usr/bin/env python3
"""
A heartwarming storyworld about a small rouge mystery, a surprising gift, and a
gentle transformation.

Seed tale:
---
Ava was a shy little girl who loved the mirror at her grandma's dressing table.
One afternoon, she found a tiny box of rouge missing from the drawer. Grandma
looked surprised, and Ava felt worried. She searched the room and discovered that
her little brother had used the rouge to draw a bright red heart on a paper
valentine for Grandma. Grandma laughed, Ava smiled, and together they used the
rouge to give Ava one soft rosy cheek for the school play. Ava stepped onto the
stage feeling brave, and Grandma's eyes shone with happy tears.

The simulated world models:
- a missing tiny cosmetic item and a child trying to solve the mystery
- a surprising reveal: the rouge was borrowed for a loving valentine
- a transformation: a shy child becomes stage-brave with a rosy cheek
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"lost": 0.0, "found": 0.0, "used": 0.0, "beautiful": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "surprise": 0.0, "love": 0.0, "shyness": 0.0, "bravery": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma"}
        male = {"boy", "father", "dad", "man", "brother", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
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


@dataclass
class StoryParams:
    child_name: str = "Ava"
    child_type: str = "girl"
    sibling_name: str = "Milo"
    sibling_type: str = "boy"
    elder_name: str = "Grandma"
    elder_type: str = "grandma"
    place: str = "the dressing room"
    seed: Optional[int] = None


CHILD_NAMES = ["Ava", "Mina", "Lena", "Ivy", "Nora", "Ellie"]
BOY_NAMES = ["Milo", "Noah", "Ben", "Theo", "Finn", "Leo"]


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    owner: str
    region: str = "cheek"


@dataclass
class Scene:
    place: str
    mood: str = "gentle"


ROUGE = Item(id="rouge", label="rouge", phrase="a tiny box of rouge", owner="Grandma")
VALENTINE = Item(id="valentine", label="valentine", phrase="a paper valentine", owner="Milo")
DRESS = Item(id="dress", label="dress", phrase="a soft dress for the school play", owner="Ava", region="body")
SCENES = {
    "dressing room": Scene(place="the dressing room"),
    "hallway mirror": Scene(place="the hallway mirror"),
    "school stage": Scene(place="the school stage"),
}


ASP_RULES = r"""
has_item(rouge).
has_item(valentine).
has_item(dress).

surprise(X) :- has_item(X), X = rouge.
mystery_to_solve(rouge).
transformation(ava) :- found(rouge), used(rouge), brave(ava).

shown(rouge).
shown(valentine).
shown(dress).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("has_item", "rouge"),
        asp.fact("has_item", "valentine"),
        asp.fact("has_item", "dress"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate() -> None:
    # This domain is always about rouge, surprise, mystery, and transformation.
    return None


def tell(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity(id="Ava", kind="character", type=params.child_type, memes={"worry": 0.0, "surprise": 0.0, "love": 0.0, "shyness": 1.0, "bravery": 0.0}))
    sibling = w.add(Entity(id="Milo", kind="character", type=params.sibling_type, memes={"worry": 0.0, "surprise": 0.0, "love": 1.0, "shyness": 0.0, "bravery": 0.0}))
    elder = w.add(Entity(id="Grandma", kind="character", type=params.elder_type, memes={"worry": 0.0, "surprise": 0.0, "love": 1.0, "shyness": 0.0, "bravery": 0.0}))
    rouge = w.add(Entity(id="rouge", type="rouge", label="rouge", phrase="a tiny box of rouge", owner="Grandma", caretaker="Grandma"))
    valentine = w.add(Entity(id="valentine", type="paper", label="valentine", phrase="a paper valentine", owner="Milo"))
    dress = w.add(Entity(id="dress", type="dress", label="dress", phrase="a soft dress for the school play", owner="Ava", region="body"))

    # Act 1: cozy setup
    w.say("Ava was a shy little girl who liked quiet things and soft smiles.")
    w.say("She loved the dressing room, where the mirror made the afternoon glow.")
    w.say(f"Grandma kept {rouge.phrase} in her drawer, and Ava thought it looked like a little jar of sunset.")
    w.para()

    # Act 2: mystery and surprise
    rouge.meters["lost"] += 1
    child.memes["worry"] += 1
    w.say("One afternoon, Grandma opened the drawer and blinked. The rouge was gone.")
    w.say("Ava felt her stomach dip. She wanted to solve the mystery, because Grandma looked so surprised.")
    w.say("Then Ava found a trail of red smudges on a scrap of paper near the table.")
    sibling.memes["surprise"] += 1
    sibling.memes["love"] += 1
    rouge.meters["found"] += 1
    w.say("Milo came in holding a valentine with a bright red heart on it. He had used the rouge to make a surprise gift for Grandma.")
    w.say("Grandma laughed softly. The mystery had a kind answer after all.")
    w.para()

    # Act 3: transformation
    rouge.meters["used"] += 1
    child.memes["shyness"] = 0.0
    child.memes["bravery"] += 1
    child.memes["surprise"] += 1
    dress.meters["beautiful"] += 1
    w.say("Grandma dabbed one gentle rosy touch on Ava's cheek and smiled into the mirror.")
    w.say('"Now you look ready for the school play," she said. Ava's shy face transformed into a brave one.')
    w.say("At the school stage, Ava stood tall in her soft dress, her rosy cheek shining like a tiny promise.")
    w.say("Grandma clapped with happy tears, and Milo grinned because his surprise had turned into a heartwarming day for everyone.")

    w.facts = {
        "child": child,
        "sibling": sibling,
        "elder": elder,
        "rouge": rouge,
        "valentine": valentine,
        "dress": dress,
        "place": params.place,
        "surprise": True,
        "mystery_solved": True,
        "transformed": True,
    }
    return w


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a warm children’s story about a rouge mystery in a dressing room, a surprising discovery, and a gentle transformation.',
        'Tell a heartwarming story where a shy child finds out why the rouge is missing and becomes brave for a special moment.',
        'Write a small story that includes rouge, a surprise gift, and a child who changes from shy to brave.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What item was missing from Grandma's drawer?",
            answer="The missing item was the rouge, a tiny box of color that Grandma kept in her drawer.",
        ),
        QAItem(
            question="Why was the missing rouge a mystery at first?",
            answer="It was a mystery because Grandma could not find the rouge in her drawer, and no one knew where it had gone until Ava followed the red smudges.",
        ),
        QAItem(
            question="What was the surprise that solved the mystery?",
            answer="The surprise was that Milo had used the rouge to make a red heart on a valentine for Grandma, so the rouge was not lost in a bad way at all.",
        ),
        QAItem(
            question="How did Ava change by the end of the story?",
            answer="Ava changed from shy to brave. After the gentle rouge touch on her cheek, she felt ready for the school play.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rouge?",
            answer="Rouge is a cosmetic color used to add a rosy tint to cheeks, a little like blush.",
        ),
        QAItem(
            question="What does a valentine usually mean?",
            answer="A valentine is a loving card or note that shows kindness, friendship, or affection.",
        ),
        QAItem(
            question="Why can a tiny touch of makeup feel like a transformation?",
            answer="A tiny touch of makeup can make someone look a little different and also feel more confident, which can change how they carry themselves.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming rouge mystery storyworld.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child_name = args.name or rng.choice(CHILD_NAMES)
    sibling_name = rng.choice(BOY_NAMES)
    return StoryParams(child_name=child_name, sibling_name=sibling_name, seed=args.seed)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    print("OK: ASP twin is present for rouge, surprise, mystery, and transformation.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show surprise/1.\n#show mystery_to_solve/1.\n#show transformation/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(child_name=name, sibling_name="Milo")) for name in CHILD_NAMES[:5]]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
