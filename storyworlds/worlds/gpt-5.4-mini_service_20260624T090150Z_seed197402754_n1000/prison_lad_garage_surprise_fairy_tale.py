#!/usr/bin/env python3
"""
storyworlds/worlds/prison_lad_garage_surprise_fairy_tale.py
============================================================

A tiny fairy-tale storyworld set in a garage, with a lad, a prison-like
surprise, and a gentle magical turn.

The seed idea:
- A lad is sorting an old garage.
- He finds a small prison that seems to hold a surprise.
- The prison is not cruel after all; it hides a little fairy.
- The lad chooses kindness, and the garage changes from dusty to bright.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- StoryParams, build_parser, resolve_params, generate, emit, main
- prose generation from simulated state
- QA sets for story-grounded and world-knowledge questions
- inline ASP twin plus Python reasonableness gate
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "lad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the garage"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class SurpriseItem:
    id: str
    label: str
    phrase: str
    type: str
    clue: str
    surprise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    surprise: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "garage": Setting(place="the garage", indoor=True, affords={"surprise"}),
}

SURPRISES = {
    "prison": SurpriseItem(
        id="prison",
        label="little prison",
        phrase="a little toy prison with a brass latch",
        type="prison",
        clue="a brass latch",
        surprise="a tiny fairy",
        tags={"prison", "fairy", "surprise"},
    ),
}

GIRL_NAMES = ["Mira", "Lily", "Ava", "Nora"]
BOY_NAMES = ["Finn", "Leo", "Owen", "Theo"]
TRAITS = ["curious", "gentle", "brave", "cheerful"]


class ASP:
    pass


ASP_RULES = r"""
% A valid story needs the garage, the lad, and the surprise prison.
valid_place(garage).
valid_surprise(prison).
valid_story(garage, prison).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("label", sid, s.label))
        for tag in sorted(s.tags):
            lines.append(asp.fact("tag", sid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [("garage", "prison")]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale garage storyworld with a lad and a surprise prison.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "garage":
        raise StoryError("This storyworld only takes place in the garage.")
    if args.surprise and args.surprise != "prison":
        raise StoryError("This storyworld only knows one surprise: the prison.")
    if args.gender and args.gender not in {"boy"}:
        raise StoryError("This tale is built for a lad; try --gender boy.")
    if args.place is None:
        args.place = "garage"
    if args.surprise is None:
        args.surprise = "prison"
    if args.gender is None:
        args.gender = "boy"
    if args.parent is None:
        args.parent = rng.choice(["mother", "father"])
    if args.name is None:
        args.name = rng.choice(BOY_NAMES)
    if args.trait is None:
        args.trait = rng.choice(TRAITS)
    return StoryParams(
        place=args.place,
        surprise=args.surprise,
        name=args.name,
        gender=args.gender,
        parent=args.parent,
        trait=args.trait,
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    lad = world.add(Entity(
        id=params.name,
        kind="character",
        type="boy",
        label="lad",
        meters={"dust": 0.0},
        memes={"wonder": 0.0, "joy": 0.0, "fear": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"dust": 0.0},
        memes={"care": 0.0},
    ))
    surprise = SURPRISES[params.surprise]
    prison = world.add(Entity(
        id="Prison",
        kind="thing",
        type="prison",
        label="little prison",
        phrase=surprise.phrase,
        owner=lad.id,
        caretaker=parent.id,
        meters={"dust": 1.0, "locked": 1.0},
        memes={"mystery": 1.0},
    ))
    fairy = world.add(Entity(
        id="Fairy",
        kind="character",
        type="fairy",
        label="fairy",
        meters={"glow": 1.0},
        memes={"sad": 1.0, "hope": 0.0},
    ))

    world.facts.update(lad=lad, parent=parent, prison=prison, fairy=fairy, surprise=surprise, params=params)

    world.say(
        f"Once in {world.setting.place}, there lived a {params.trait} lad named {lad.id} who loved tidy shelves and shiny bolts."
    )
    world.say(
        f"On the highest shelf sat {prison.phrase}, and no one had opened {prison.it()} for a long, long while."
    )

    world.para()
    lad.memes["wonder"] += 1
    world.say(
        f"{lad.id} noticed {surprise.clue} on the latch and leaned closer, for the little prison seemed to hide a surprise."
    )
    world.say(
        f"{parent.label.capitalize()} warned him that old things can snap, but {lad.id} held the box gently with both hands."
    )

    world.para()
    lad.meters["dust"] += 1
    lad.memes["fear"] += 1
    world.say(
        f"When {lad.id} brushed away the dust, the latch clicked, and a tiny light blinked from inside."
    )
    world.say(
        f"To {lad.id}'s great surprise, the prison held {surprise.surprise}, not a wicked thing at all."
    )
    fairy.memes["hope"] += 1
    fairy.memes["sad"] = 0.0

    world.para()
    lad.memes["joy"] += 2
    prison.meters["locked"] = 0.0
    prison.memes["mystery"] = 0.0
    world.say(
        f"{lad.id} opened the little prison and let the fairy out, and the garage grew bright as a lantern room."
    )
    world.say(
        f"The fairy sang a merry tune, dust lifted from the rafters, and {parent.label} smiled at the brave lad."
    )
    world.say(
        f"By evening, the prison stood open on the shelf, the fairy fluttered safely by the tools, and {lad.id} had turned a surprise into a kindness."
    )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    surprise: SurpriseItem = f["surprise"]
    return [
        f'Write a short fairy-tale story about a lad in the garage who finds a {surprise.label}.',
        f"Tell a gentle story where {params.name} notices a surprise on an old shelf and chooses kindness.",
        f'Write a child-friendly tale that uses the word "{surprise.id}" and ends with a magical change in the garage.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    surprise: SurpriseItem = f["surprise"]
    lad: Entity = f["lad"]
    parent: Entity = f["parent"]
    prison: Entity = f["prison"]
    fairy: Entity = f["fairy"]
    return [
        QAItem(
            question=f"Who is the story about in the garage?",
            answer=f"It is about a lad named {params.name}, along with {parent.label}, who finds {prison.label}.",
        ),
        QAItem(
            question=f"What was hidden in the little prison?",
            answer=f"The little prison held {surprise.surprise}. That is why the prison was a surprise in the garage.",
        ),
        QAItem(
            question=f"How did {lad.id} change the prison at the end?",
            answer=f"{lad.id} opened it gently, and the locked prison became an open place where the fairy could flutter safely.",
        ),
        QAItem(
            question=f"Why did the garage feel different after the prison was opened?",
            answer=f"The garage felt bright and merry because the fairy sang, the dust lifted, and everyone saw that the surprise was kind, not cruel.",
        ),
        QAItem(
            question=f"How did the fairy feel when {lad.id} helped?",
            answer=f"The fairy was no longer sad. After {lad.id} helped, the fairy felt hope and flew happily by the tools.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garage?",
            answer="A garage is a building or room where people often keep a car, tools, bikes, and other useful things.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect. It can feel exciting, strange, or joyful when it appears suddenly.",
        ),
        QAItem(
            question="What is a fairy in fairy tales?",
            answer="A fairy in fairy tales is a tiny magical being, often with wings, who can sparkle, sing, or use gentle magic.",
        ),
        QAItem(
            question="Why should old things in a garage be handled carefully?",
            answer="Old things can be dusty, stiff, or fragile, so it is wise to touch them gently and slowly.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="garage", surprise="prison", name="Finn", gender="boy", parent="father", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, surprise in combos:
            print(f"  {place:10} {surprise}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
