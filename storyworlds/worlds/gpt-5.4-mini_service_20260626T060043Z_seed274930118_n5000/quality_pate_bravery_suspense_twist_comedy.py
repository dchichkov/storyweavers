#!/usr/bin/env python3
"""
storyworlds/worlds/quality_pate_bravery_suspense_twist_comedy.py
=================================================================

A small, self-contained storyworld about a brave kitchen mishap:
a child, a fancy pate, a suspenseful moment, and a silly twist.

The world is built to generate short, child-facing comedy stories with:
- a clear setup
- a tense middle
- a twisty, funny resolution

The seed words for this world are "quality" and "pate".
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
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    risk: str
    tag: str


@dataclass
class CharacterSpec:
    name: str
    type: str
    parent_type: str


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"mix", "carry"}),
    "pantry": Setting(place="the pantry", affords={"mix"}),
    "picnic": Setting(place="the picnic table", affords={"carry"}),
}

ITEMS = {
    "quality_pate": Item(
        id="quality_pate",
        label="quality pate",
        phrase="a small dish of quality pate",
        kind="pate",
        risk="spill",
        tag="pate",
    ),
    "silver_spoon": Item(
        id="silver_spoon",
        label="silver spoon",
        phrase="a shiny silver spoon",
        kind="spoon",
        risk="clatter",
        tag="spoon",
    ),
    "paper_hat": Item(
        id="paper_hat",
        label="paper chef hat",
        phrase="a paper chef hat",
        kind="hat",
        risk="crumple",
        tag="hat",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Ben", "Leo", "Theo", "Max", "Finn"]
TRAITS = ["brave", "curious", "silly", "cheery", "bouncy"]


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
at_risk(Item) :- item(Item), risk(Item, Spill), setting_place(Place), carried(Item), spoils(Spill, Place).
has_fix(Item) :- at_risk(Item), fix_available(Item).
valid_story(Place, Item, Gender) :- setting(Place), item(Item), has_fix(Item), wears(Gender, Item).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("risk", iid, it.risk))
        lines.append(asp.fact("tag", iid, it.tag))
    lines.append(asp.fact("fix_available", "quality_pate"))
    lines.append(asp.fact("wears", "girl", "quality_pate"))
    lines.append(asp.fact("wears", "boy", "quality_pate"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    return [(place, item) for place, s in SETTINGS.items() for item in ITEMS if item == "quality_pate"]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about bravery, suspense, and a twisty pate.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.item and args.item != "quality_pate":
        raise StoryError("This world only tells stories about quality pate.")
    if args.gender and args.name is None:
        pass
    combos = ["quality_pate"]
    if not combos:
        raise StoryError("No valid story combination.")
    place = args.place or rng.choice(list(SETTINGS))
    item = "quality_pate"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, item=item, name=name, gender=gender, parent=parent, trait=trait)


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    pate = world.add(Entity(
        id="pate",
        type="thing",
        label="quality pate",
        phrase="a small dish of quality pate",
        owner=hero.id,
        caretaker=parent.id,
    ))
    spoon = world.add(Entity(id="spoon", type="thing", label="silver spoon", phrase="a shiny silver spoon", owner=hero.id))
    hat = world.add(Entity(id="hat", type="thing", label="paper chef hat", phrase="a paper chef hat", owner=hero.id))

    hero.memes["bravery"] = 0.0
    hero.memes["suspense"] = 0.0
    hero.memes["joy"] = 0.0

    world.say(f"{hero.id} was a {params.trait} little {params.gender} who loved tiny kitchen adventures.")
    world.say(f"One day, {hero.id}'s {parent.pronoun('possessive') if False else params.parent} promised a special treat: {pate.phrase}.")
    world.say(f"{hero.id} liked the funny fancy smell of the {pate.label} and held {hero.pronoun('possessive')} breath like a brave captain.")

    world.para()
    world.say(f"At {world.setting.place}, {hero.id} wanted to carry the {pate.label} to the table.")
    hero.memes["bravery"] += 1
    hero.memes["suspense"] += 1
    world.say(f"{hero.pronoun().capitalize()} walked carefully, because the spoon wobbled and the hat leaned sideways like a sleepy pancake.")

    world.say(f"Then the {spoon.label} made a tiny clink-clink sound, and everyone froze for a second.")
    world.say(f"{hero.id} thought the {pate.label} might splat, but {hero.id} kept going anyway.")
    world.say(f"That was the brave part, and it was also a little silly.")

    world.para()
    world.say(f"{params.parent.capitalize()} peeked under the hat and laughed.")
    world.say(f"The big suspenseful twist was this: the special judge was not a royal prince at all.")
    world.say(f"It was a very serious squirrel in a napkin cape, waiting for a crumb.")

    world.say(f"{hero.id} giggled so hard that the spoon almost danced by itself.")
    world.say(f"The squirrel approved the {pate.label}, and {hero.id} learned that a brave heart can make a tiny dinner feel grand.")
    world.say(f"In the end, the {pate.label} stayed neat, the hat stayed on sideways, and everybody smiled at the ridiculous little feast.")

    world.facts.update(hero=hero, parent=parent, pate=pate, spoon=spoon, hat=hat, params=params, setting=world.setting)
    return world


def generate_story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a short comedy story for a child about {hero.id}, bravery, suspense, and a quality pate.",
        f"Tell a funny story where {hero.id} carries a quality pate carefully and discovers a surprising twist.",
        f"Create a gentle kitchen story with a brave child, a wobbly spoon, and a silly ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, pate = f["hero"], f["parent"], f["pate"]
    return [
        QAItem(
            question=f"Who was the brave child in the story?",
            answer=f"The brave child was {hero.id}. {hero.id} carried the quality pate carefully and kept going.",
        ),
        QAItem(
            question=f"What special dish did {hero.id} carry?",
            answer=f"{hero.id} carried a dish of quality pate.",
        ),
        QAItem(
            question="What was the silly twist at the end?",
            answer="The special judge turned out to be a very serious squirrel in a napkin cape.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful?",
            answer=f"It felt suspenseful because the spoon wobbled and everyone worried the quality pate might splat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pate?",
            answer="Pate is a smooth spread or paste made from cooked ingredients, often served as a fancy snack or treat.",
        ),
        QAItem(
            question="What does quality mean?",
            answer="Quality means something is made well and works or tastes very nicely.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone does something even though they feel a little scared.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting and wondering what will happen next.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that the reader did not expect.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=generate_story_text(world),
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(place="kitchen", item="quality_pate", name="Mia", gender="girl", parent="mother", trait="brave")
        samples = [generate(params)]
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
