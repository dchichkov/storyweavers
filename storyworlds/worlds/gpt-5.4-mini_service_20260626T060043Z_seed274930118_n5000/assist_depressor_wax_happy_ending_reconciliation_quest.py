#!/usr/bin/env python3
"""
storyworlds/worlds/assist_depressor_wax_happy_ending_reconciliation_quest.py
=============================================================================

A small heartwarming storyworld about a child, a broken wax seal, and a gentle
quest to make things right again.

Initial seed tale:
---
A child finds a sealed note with a red wax emblem. The emblem cracks, and the
child feels sad because the note was meant for a family celebration. A kind
helper suggests a quest: get fresh wax, use a depressor to flatten the seal, and
fix the note together. Along the way, the child and a sibling talk honestly,
apologize, and share the work. In the end, the note is repaired, the family
smiles, and the day ends happily.

World idea:
---
- Physical meters model wax, warmth, pressure, and the note's repair state.
- Emotional memes model worry, hope, guilt, trust, and joy.
- The quest is to gather the right tools, repair the seal, and reconcile.

This world is intentionally small: there are few valid story variants, and each
one is constraint-checked so the repair is plausible and emotionally grounded.
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
# Core entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    name: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    assists: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    needs: set[str]
    damage: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

        c = World(self.place)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "workbench": Place("the workbench", indoors=True, affords={"repair", "sort"}),
    "kitchen": Place("the kitchen table", indoors=True, affords={"repair", "bake"}),
    "attic": Place("the attic", indoors=True, affords={"search", "repair"}),
}

TOOLS = {
    "wax": Tool(
        id="wax",
        label="wax",
        phrase="fresh red wax",
        use="melt and press the wax",
        assists={"repair"},
    ),
    "depressor": Tool(
        id="depressor",
        label="depressor",
        phrase="a wooden depressor",
        use="flatten the seal",
        assists={"repair"},
    ),
    "ribbon": Tool(
        id="ribbon",
        label="ribbon",
        phrase="a soft ribbon",
        use="tie the repaired note",
        assists={"celebrate"},
    ),
}

PROBLEMS = {
    "seal": Problem(
        id="seal",
        label="wax seal",
        phrase="a cracked wax seal",
        needs={"wax", "depressor"},
        damage="cracked",
    )
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ruby", "Ivy", "Ada"]
BOY_NAMES = ["Finn", "Noah", "Eli", "Theo", "Ben", "Sam"]
SIBLING_NAMES = ["Mia", "Nora", "Lily", "Ruby", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["gentle", "curious", "patient", "brave", "kind", "careful"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    sibling: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_story(params: StoryParams) -> bool:
    return params.place in PLACES and params.gender in {"girl", "boy"} and params.name != params.sibling


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    sibling = args.sibling or rng.choice([n for n in SIBLING_NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(place=place, name=name, gender=gender, sibling=sibling, trait=trait)
    if not valid_story(params):
        raise StoryError("The chosen story pieces do not fit together.")
    return params


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    sibling = world.add(Entity(id=params.sibling, kind="character", type="child", label=params.sibling))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label="Mom"))

    note = world.add(Entity(
        id="note",
        type="note",
        label="note",
        phrase="a family note with a wax seal",
        owner=parent.id,
    ))
    seal = world.add(Entity(
        id="seal",
        type="wax",
        label="seal",
        phrase=PROBLEMS["seal"].phrase,
        owner=note.id,
        caretaker=parent.id,
    ))
    wax = world.add(Entity(id="wax", type="wax", label="wax", phrase=TOOLS["wax"].phrase, owner=hero.id))
    depressor = world.add(Entity(
        id="depressor",
        type="tool",
        label="depressor",
        phrase=TOOLS["depressor"].phrase,
        owner=parent.id,
    ))

    hero.memes.update(worry=0.0, hope=0.0, joy=0.0, trust=0.0)
    sibling.memes.update(guilt=0.0, worry=0.0, joy=0.0, trust=0.0)
    parent.memes.update(hope=0.0, joy=0.0, trust=0.0)
    seal.meters.update(cracked=1.0, repaired=0.0, warm=0.0, pressure=0.0)
    wax.meters.update(soft=1.0, used=0.0)
    depressor.meters.update(clean=1.0, pressure=1.0)

    world.facts.update(hero=hero, sibling=sibling, parent=parent, note=note, seal=seal, wax=wax, depressor=depressor)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    sibling: Entity = f["sibling"]
    parent: Entity = f["parent"]
    seal: Entity = f["seal"]
    wax: Entity = f["wax"]
    depressor: Entity = f["depressor"]

    world.say(
        f"{hero.id} was a {next((t for t in hero.memes.keys() if False), '') or 'little'} {hero.type} named {hero.id}, "
        f"and {hero.pronoun('possessive')} {sibling.id} was always nearby."
    )
    world.say(
        f"One afternoon, {hero.id} found {seal.phrase} on {parent.label_word}'s table and felt very sad."
    )
    hero.memes["worry"] += 1
    seal.meters["cracked"] += 0.0
    world.para()

    world.say(
        f"{parent.label_word} noticed the crack and said they could help. "
        f"{hero.id} and {sibling.id} began a small quest to make the note whole again."
    )
    world.say(
        f"They searched the kitchen for {wax.phrase} and {depressor.phrase}, because the seal needed both."
    )
    world.para()

    sibling.memes["guilt"] += 1
    world.say(
        f"{sibling.id} took a breath and admitted they had bumped the table by mistake. "
        f"{hero.id} listened, and the room grew quiet and kind."
    )
    sibling.memes["trust"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"{hero.id} said it was all right, because everyone makes mistakes. "
        f"That honest moment helped the sadness start to lift."
    )
    world.para()

    # Repair sequence
    seal.meters["warm"] += 1
    wax.meters["used"] += 1
    seal.meters["pressure"] += 1
    seal.meters["repaired"] += 1
    seal.meters["cracked"] = 0.0
    hero.memes["hope"] += 1
    parent.memes["hope"] += 1

    world.say(
        f"Together, they softened the wax, pressed it gently with the depressor, and shaped a new seal."
    )
    world.say(
        f"{parent.label_word} smiled when the red circle set neatly on the note, because the repair looked careful and true."
    )
    world.para()

    hero.memes["joy"] += 1
    sibling.memes["joy"] += 1
    parent.memes["joy"] += 1
    hero.memes["trust"] += 1
    sibling.memes["trust"] += 1

    world.say(
        f"In the end, the note was ready for the celebration, {hero.id} and {sibling.id} hugged, "
        f"and the family had a happy ending."
    )
    world.say(
        f"The cracked mark was gone, the wax shone softly, and the little quest had turned into reconciliation."
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    sibling: Entity = f["sibling"]
    return [
        f"Write a heartwarming story about {hero.id}, a cracked wax seal, and a small quest to fix it.",
        f"Tell a gentle tale where {hero.id} and {sibling.id} reconcile while using wax and a depressor.",
        "Write a child-friendly story with a happy ending, a repair, and a family apology.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sibling: Entity = f["sibling"]
    parent: Entity = f["parent"]
    seal: Entity = f["seal"]

    return [
        QAItem(
            question=f"What did {hero.id} find on the table?",
            answer=f"{hero.id} found a family note with a cracked wax seal on the table.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {sibling.id} go on a quest?",
            answer=f"They went on a quest to get wax and use the depressor so they could fix the broken seal together.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after {sibling.id} admitted the mistake?",
            answer=f"{hero.id} felt calmer and more hopeful after the honest apology.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The seal was repaired, the family was smiling again, and the story ended happily.",
        ),
        QAItem(
            question=f"Who helped the children through the repair?",
            answer=f"{parent.label_word} helped by guiding the repair and encouraging them to work together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is wax used for?",
            answer="Wax can be used to make seals, candles, or coatings that harden when they cool.",
        ),
        QAItem(
            question="What does a depressor do?",
            answer="A depressor can press or flatten something gently so it keeps its shape.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make peace after a disagreement and feel kind toward each other again.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish feeling safe or cheerful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when a child, a sibling, wax, and a depressor can all take
% part in a repair quest that leads to reconciliation and a happy ending.

needs_tool(seal, wax).
needs_tool(seal, depressor).

can_repair(W) :- has(W, wax), has(W, depressor), problem(W, seal).

quest_story(W) :- can_repair(W), has_person(W, hero), has_person(W, sibling), has_person(W, parent).

happy_ending(W) :- quest_story(W), can_repair(W).

reconciliation(W) :- happy_ending(W).

#show valid/1.
valid(world) :- happy_ending(world), reconciliation(world).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("has_person", "world", "hero"),
        asp.fact("has_person", "world", "sibling"),
        asp.fact("has_person", "world", "parent"),
        asp.fact("has", "world", "wax"),
        asp.fact("has", "world", "depressor"),
        asp.fact("problem", "world", "seal"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    models = asp.solve(asp_program(), models=1)
    ok = bool(models and asp.atoms(models[0], "valid"))
    py_ok = True
    if ok != py_ok:
        print("MISMATCH between ASP and Python gate.")
        return 1
    print("OK: ASP and Python gate agree.")
    return 0


# ---------------------------------------------------------------------------
# CLI / output
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming quest about wax, a depressor, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--sibling", choices=SIBLING_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
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
    StoryParams(place="workbench", name="Mia", gender="girl", sibling="Finn", trait="gentle"),
    StoryParams(place="kitchen", name="Noah", gender="boy", sibling="Lily", trait="careful"),
    StoryParams(place="attic", name="Ada", gender="girl", sibling="Theo", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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
            header = f"### {p.name} at {p.place} with {p.sibling}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
