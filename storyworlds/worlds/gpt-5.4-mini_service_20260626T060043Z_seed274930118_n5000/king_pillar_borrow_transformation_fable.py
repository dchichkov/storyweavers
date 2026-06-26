#!/usr/bin/env python3
"""
storyworlds/worlds/king_pillar_borrow_transformation_fable.py
==============================================================

A small fable-like story world about a king, a pillar, and a borrowed thing
that changes shape, purpose, or heart.

Premise:
- A proud king sees a need and borrows a plain pillar.
- The pillar is meant to support something in the realm.
- The work causes a pressure or imbalance.
- A wise choice turns the borrowed pillar into a new form of help.

The world is intentionally tiny: one king, one location, one borrowed object,
and one transformation that resolves the trouble. The prose is child-facing and
moralistic, in the style of a short fable.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    borrower: Optional[str] = None
    place: str = ""
    transformed: bool = False
    borrowed: bool = False
    returned: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectKind:
    id: str
    label: str
    phrase: str
    material: str
    transformation: str
    uses: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    object_kind: str
    king_name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "courtyard": Setting(place="the castle courtyard", affords={"support", "display"}),
    "hall": Setting(place="the grand hall", affords={"support", "display"}),
    "garden": Setting(place="the palace garden", affords={"support", "display"}),
}

OBJECTS = {
    "pillar": ObjectKind(
        id="pillar",
        label="pillar",
        phrase="a carved stone pillar",
        material="stone",
        transformation="banner stand",
        uses={"support", "display"},
    ),
    "stool": ObjectKind(
        id="stool",
        label="stool",
        phrase="a wooden stool",
        material="wood",
        transformation="step stool",
        uses={"support", "reach"},
    ),
    "ladder": ObjectKind(
        id="ladder",
        label="ladder",
        phrase="a tall ladder",
        material="wood",
        transformation="bridge",
        uses={"reach", "support"},
    ),
}

TRAITS = ["proud", "patient", "curious", "kind", "vain", "gentle"]
KING_NAMES = ["Arin", "Borin", "Cai", "Dorian", "Elias", "Felix"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/2.
#show transform/3.

valid(P, O) :- place(P), object(O), supports(P, O), useful(O).
transform(O, From, To) :- object(O), morphs(O, From, To).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("supports", sid, a))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("useful", oid))
        lines.append(asp.fact("morphs", oid, o.material, o.transformation))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_transforms() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show transform/3."))
    return sorted(set(asp.atoms(model, "transform")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
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
# Logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for oid, obj in OBJECTS.items():
            if "support" in setting.affords and "support" in obj.uses:
                combos.append((place, oid))
    return combos


def explain_rejection(place: str, oid: str) -> str:
    return (
        f"(No story: the {oid} cannot make a fable at {place} because that place "
        f"does not support the kind of help the object offers.)"
    )


def build_story_text(world: World) -> None:
    king = world.get("king")
    obj = world.get("borrowed")
    trait = king.memes.get("trait_word", "proud")
    place = world.setting.place

    world.say(
        f"In {place}, there lived a {trait} king named {king.label}."
    )
    world.say(
        f"He wished to show everyone that his realm was grand, and he admired "
        f"{obj.phrase} for its steady shape."
    )
    world.say(
        f"One day he asked to borrow the {obj.label}, and the keeper agreed, "
        f"for a good thing can be shared when it is used wisely."
    )
    obj.borrowed = True
    obj.borrower = king.id
    king.memes["desire"] = king.memes.get("desire", 0) + 1

    world.say(
        f"The king carried the {obj.label} to the {place} and set it where it "
        f"could help."
    )

    # A small tension: the borrowed thing is good, but its old purpose is not enough.
    king.meters["work"] = king.meters.get("work", 0) + 1
    obj.meters["strain"] = obj.meters.get("strain", 0) + 1

    if obj.id == "pillar":
        world.say(
            f"At first, the plain pillar only stood there. Then the king saw that "
            f"it could become a banner stand, and that change made the whole court "
            f"look brighter."
        )
        obj.transformed = True
        obj.label = "banner stand"
        obj.phrase = "a banner stand made from the borrowed pillar"
        king.memes["humility"] = king.memes.get("humility", 0) + 1
    elif obj.id == "stool":
        world.say(
            f"At first, the stool was too short. So the king turned it into a "
            f"step stool, and then the smallest child could reach the fruit basket."
        )
        obj.transformed = True
        obj.label = "step stool"
        obj.phrase = "a step stool made from the borrowed stool"
        king.memes["humility"] = king.memes.get("humility", 0) + 1
    else:
        world.say(
            f"At first, the ladder was too narrow for the king's proud plan. "
            f"Then he used it as a bridge for workers carrying branches, and the "
            f"whole task became easier."
        )
        obj.transformed = True
        obj.label = "bridge"
        obj.phrase = "a little bridge made from the borrowed ladder"
        king.memes["humility"] = king.memes.get("humility", 0) + 1

    obj.returned = True
    world.say(
        f"When the work was done, the king returned the borrowed thing with care, "
        f"because borrowing is fair only when returning follows."
    )
    world.say(
        f"That night the people smiled, and the king learned that a good ruler is "
        f"not made by owning more, but by changing a humble thing into a help for all."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about a king named {f["king"].label} who borrows a {f["object_kind"].label} and learns a lesson.',
        f"Tell a child-friendly story where a {f['trait']} king borrows {f['object_kind'].phrase} and it changes into something useful.",
        f'Write a simple moral tale using the words "king", "pillar", and "borrow".',
    ]


def story_qa(world: World) -> list[QAItem]:
    king = world.facts["king"]
    obj = world.facts["object"]
    kind = world.facts["object_kind"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about King {king.label}, who borrowed {kind.label} and learned a gentle lesson.",
        ),
        QAItem(
            question=f"What did the king borrow?",
            answer=f"He borrowed {kind.phrase} from the keeper, and later it became {obj.label}.",
        ),
        QAItem(
            question=f"What changed about the borrowed thing?",
            answer=f"It transformed from {kind.label} into {obj.label}, so it could help in a new way.",
        ),
        QAItem(
            question=f"What did the king learn at the end?",
            answer=(
                "He learned that borrowing should be done carefully, and that even a plain thing "
                "can become useful when it is used with wisdom."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pillar?",
            answer="A pillar is a tall, strong column that can hold up weight or stand as a marker.",
        ),
        QAItem(
            question="What does borrow mean?",
            answer="To borrow means to take something for a while and then give it back.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or purpose into another.",
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


# ---------------------------------------------------------------------------
# Generate / emit
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    kind = OBJECTS[params.object_kind]
    world = World(setting)
    king = world.add(Entity(
        id="king",
        kind="character",
        type="king",
        label=params.king_name,
        place=setting.place,
        meters={"rule": 1.0},
        memes={"trait_word": params.trait},
    ))
    borrowed = world.add(Entity(
        id="borrowed",
        kind="thing",
        type=kind.id,
        label=kind.label,
        phrase=kind.phrase,
        owner="keeper",
        borrowed=True,
        place=setting.place,
        meters={"weight": 1.0},
    ))
    world.facts = {
        "king": king,
        "object": borrowed,
        "object_kind": kind,
        "trait": params.trait,
        "place": setting.place,
    }
    build_story_text(world)
    return world


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
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.borrowed:
            bits.append("borrowed=True")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
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


# ---------------------------------------------------------------------------
# Params and CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="courtyard", object_kind="pillar", king_name="Arin", trait="proud"),
    StoryParams(place="hall", object_kind="stool", king_name="Borin", trait="curious"),
    StoryParams(place="garden", object_kind="ladder", king_name="Cai", trait="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small fable world about a king, a borrowed object, and a transformation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object-kind", choices=OBJECTS)
    ap.add_argument("--name", dest="king_name")
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
    if args.place and args.object_kind:
        if (args.place, args.object_kind) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.object_kind))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.object_kind is None or c[1] == args.object_kind)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, object_kind = rng.choice(sorted(combos))
    king_name = args.king_name or rng.choice(KING_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, object_kind=object_kind, king_name=king_name, trait=trait)


def asp_program_full(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program_full("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_transforms() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program_full("#show transform/3."))
    return sorted(set(asp.atoms(model, "transform")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_full("#show valid/2.\n#show transform/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, object) combos:\n")
        for place, oid in combos:
            print(f"  {place:10} {oid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.king_name}: {p.object_kind} at {p.place} ({p.trait})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
