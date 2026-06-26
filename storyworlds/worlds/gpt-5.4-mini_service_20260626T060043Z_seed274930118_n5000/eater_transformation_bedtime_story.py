#!/usr/bin/env python3
"""
storyworlds/worlds/eater_transformation_bedtime_story.py
========================================================

A bedtime story world about a little eater, a warm snack, and a gentle
transformation that helps the night feel safe and sleepy.

Premise:
- A child-like eater is hungry at bedtime.
- A cozy snack is brought out.
- The snack can transform the eater's feeling, shape, or bedtime space.
- The story turns on choosing the right transformation and settling into sleep.

The world is small on purpose: a few entities, one bedtime conflict, one
magical turn, and a calm ending image.
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
# World constants
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedroom"
    cozy: str = "soft lamp light"
    affords: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    taste: str
    effect: str
    transform_to: str
    bedtime: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    label: str
    change: str
    helps: str
    result_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bedroom": Setting(place="the bedroom", cozy="a soft yellow lamp", affords={"snack", "story"}),
    "nursery": Setting(place="the nursery", cozy="a moon-shaped nightlight", affords={"snack", "story"}),
    "cottage": Setting(place="the cottage bedroom", cozy="a quilt and a small candle", affords={"snack", "story"}),
}

SNACKS = {
    "oatmeal": Snack(
        id="oatmeal",
        label="oatmeal",
        phrase="a warm bowl of oatmeal with honey",
        taste="sweet",
        effect="settled the tummy",
        transform_to="sleepy",
        tags={"warm", "food"},
    ),
    "banana": Snack(
        id="banana",
        label="banana mash",
        phrase="a little bowl of banana mash",
        taste="soft",
        effect="smoothed the grumbles away",
        transform_to="gentle",
        tags={"food", "soft"},
    ),
    "toast": Snack(
        id="toast",
        label="toast",
        phrase="buttered toast cut into small stars",
        taste="toasty",
        effect="made the room feel warmer",
        transform_to="cozy",
        tags={"food", "warm"},
    ),
}

TRANSFORMS = {
    "sleepy": Transformation(
        id="sleepy",
        label="sleepy",
        change="the eater's eyes grew heavy",
        helps="bedtime came easier",
        result_image="the little eater curled up like a tiny kitten",
        tags={"sleep", "bedtime"},
    ),
    "gentle": Transformation(
        id="gentle",
        label="gentle",
        change="the eater's hands moved softly and slowly",
        helps="the last bit of fussing faded away",
        result_image="the little eater rested with a quiet smile",
        tags={"calm"},
    ),
    "cozy": Transformation(
        id="cozy",
        label="cozy",
        change="the whole room seemed to fluff up and warm itself",
        helps="everything felt safe and snug",
        result_image="the little eater tucked under the blanket with rosy cheeks",
        tags={"warm", "home"},
    ),
}

NAMES = ["Milo", "Nina", "Pip", "Luna", "Toby", "Mira", "Jun", "Ada", "Noah", "Ivy"]
GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father"]
TRAITS = ["sleepy", "curious", "small", "gentle", "wobbly"]


@dataclass
class StoryParams:
    place: str
    snack: str
    transform: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "snack" not in setting.affords:
            continue
        for snack_id, snack in SNACKS.items():
            for tid, tr in TRANSFORMS.items():
                if snack.transform_to == tr.id:
                    combos.append((place, snack_id, tid))
    return combos


def explain_rejection(snack: Snack, tr: Transformation) -> str:
    return (
        f"(No story: {snack.label} does not lead to the {tr.label} transformation "
        f"in this tiny bedtime world. Pick a snack and transformation that match.)"
    )


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _reset_tension(world: World, eater: Entity) -> None:
    eater.memes["fuss"] = 0.0


def _eat_snack(world: World, eater: Entity, snack: Snack, tr: Transformation, narrate: bool = True) -> None:
    eater.meters["full"] = eater.meters.get("full", 0.0) + 1.0
    eater.memes["hunger"] = max(0.0, eater.memes.get("hunger", 0.0) - 1.0)
    eater.memes["comfort"] = eater.memes.get("comfort", 0.0) + 1.0
    eater.memes["sleepy"] = eater.memes.get("sleepy", 0.0) + 1.0
    eater.memes["transformed"] = eater.memes.get("transformed", 0.0) + 1.0
    if narrate:
        world.say(
            f"{eater.id} ate the {snack.label}, and {snack.effect}."
        )
        world.say(
            f"Then {tr.change}, and {tr.helps}."
        )
        world.say(
            f"At the end, {tr.result_image}."
        )


def tell(setting: Setting, snack: Snack, tr: Transformation,
         hero_name: str = "Milo", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    eater = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["sleepy", "gentle"]),
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=f"the {parent_type}",
    ))
    bowl = world.add(Entity(
        id="Snack",
        type=snack.id,
        label=snack.label,
        phrase=snack.phrase,
        owner=eater.id,
        caretaker=parent.id,
    ))

    eater.memes["hunger"] = 1.0
    eater.memes["fuss"] = 1.0

    world.say(
        f"{eater.id} was a little {hero_type} who got hungry when bedtime came."
    )
    world.say(
        f"{hero_name}'s {parent_type} brought {bowl.phrase} to {setting.place}."
    )
    world.say(
        f"Under {setting.cozy}, {eater.id} wanted to stay up just a tiny bit longer."
    )

    world.para()
    if snack.bedtime:
        world.say(
            f"But first came one warm bite, and that bite could change things."
        )
    _eat_snack(world, eater, snack, tr, narrate=True)

    world.para()
    _reset_tension(world, eater)
    world.say(
        f"{eater.id} blinked slowly, listened to the quiet room, and snuggled down."
    )
    world.say(
        f"{eater.id} was no longer fussy; {eater.pronoun('subject')} was ready for sleep."
    )

    world.facts.update(
        eater=eater,
        parent=parent,
        snack=snack,
        transform=tr,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    eater = f["eater"]
    snack = f["snack"]
    tr = f["transform"]
    return [
        f'Write a gentle bedtime story about a little eater named {eater.id} and {snack.label}.',
        f"Tell a cozy story where {eater.id} eats {snack.phrase} and becomes {tr.label}.",
        f'Write a short bedtime tale that includes "{snack.label}" and a quiet transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    eater, parent, snack, tr = f["eater"], f["parent"], f["snack"], f["transform"]
    trait = next((t for t in eater.traits if t != "little"), eater.type)
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {eater.id}, a little {trait} {eater.type}, and {parent.label}.",
        ),
        QAItem(
            question=f"What did {eater.id} eat at bedtime?",
            answer=f"{eater.id} ate {snack.phrase}.",
        ),
        QAItem(
            question=f"What changed after {eater.id} ate the snack?",
            answer=f"{eater.id} became {tr.label}, so bedtime felt easier and calmer.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {eater.id} sleepy, tucked down, and ready to fall asleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bedtime for?",
            answer="Bedtime is the time when a child gets washed, snuggled in, and gets ready to sleep.",
        ),
        QAItem(
            question="What does cozy mean?",
            answer="Cozy means warm, safe, and comfortable, like a soft blanket on a quiet night.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state into another, like sleepy feelings becoming calm ones.",
        ),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
snack(S) :- snack_fact(S).
transform(T) :- transform_fact(T).
place(P) :- place_fact(P).

compatible(P,S,T) :- place(P), snack(S), transform(T), snack_leads_to(S,T).
valid(P,S,T) :- compatible(P,S,T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place_fact", pid))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack_fact", sid))
        lines.append(asp.fact("snack_leads_to", sid, snack.transform_to))
    for tid in TRANSFORMS:
        lines.append(asp.fact("transform_fact", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a little eater, a snack, and a gentle transformation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.snack and args.transform:
        snack = SNACKS[args.snack]
        tr = TRANSFORMS[args.transform]
        if snack.transform_to != tr.id:
            raise StoryError(explain_rejection(snack, tr))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.snack is None or c[1] == args.snack)
              and (args.transform is None or c[2] == args.transform)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, snack_id, transform_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        snack=snack_id,
        transform=transform_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        SNACKS[params.snack],
        TRANSFORMS[params.transform],
        params.name,
        params.gender,
        [params.trait],
        params.parent,
    )
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
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
    StoryParams(place="bedroom", snack="oatmeal", transform="sleepy", name="Milo", gender="boy", parent="mother", trait="sleepy"),
    StoryParams(place="nursery", snack="banana", transform="gentle", name="Luna", gender="girl", parent="father", trait="gentle"),
    StoryParams(place="cottage", snack="toast", transform="cozy", name="Ivy", gender="girl", parent="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible combos:")
        for v in vals:
            print(" ", v)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
