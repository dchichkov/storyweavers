#!/usr/bin/env python3
"""
A standalone storyworld for a tiny rhyming tale about a curious plant, a butler,
and a croissant.

The world model tracks:
- physical meters: thirst, crumbs, warmth, polish
- emotional memes: curiosity, patience, pride, delight

The generated stories are small, child-facing, and state-driven: the plant gets
curious, repeats a little action, the butler notices a problem, and a gentle
fix resolves it.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["thirst", "crumbs", "warmth", "polish"]:
            self.meters.setdefault(key, 0.0)
        for key in ["curiosity", "patience", "pride", "delight", "worry", "repetition"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"butler", "man", "father", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "mother", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Story knobs
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    name: str
    seed: Optional[int] = None


SETTINGS = {
    "sunroom": "the sunroom",
    "kitchen": "the kitchen",
    "hall": "the hall",
    "tearoom": "the tearoom",
}

NAMES = ["Pip", "Milo", "Nina", "Tia", "Ollie", "Rosa"]
BUTLER_NAMES = ["Mr. Bram", "Mr. Bell", "Mr. Taffy"]


# ---------------------------------------------------------------------------
# Narrative state
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(place=SETTINGS[params.place])

    plant = world.add(Entity(
        id=params.name,
        kind="character",
        type="plant",
        label="plant",
        phrase="a little potted plant",
    ))
    butler = world.add(Entity(
        id="Butler",
        kind="character",
        type="butler",
        label=random.choice(BUTLER_NAMES) if params.seed is not None else "the butler",
        phrase="a careful butler",
    ))
    croissant = world.add(Entity(
        id="Croissant",
        type="croissant",
        label="croissant",
        phrase="a buttery croissant",
        owner=butler.id,
        caretaker=butler.id,
    ))

    # Act 1: setup
    world.say(f"{plant.id} was a little plant in {world.place}.")
    world.say(
        f"{plant.id} was full of curiosity, and the day felt bright and spry; "
        f"{plant.id} liked to peek and peer and ask, “What, why, and how, oh my?”"
    )
    world.say(
        f"The butler kept a buttery croissant on a small round tray, warm and neat, "
        f"for tea-time smiles and tidy lines and crumbs that must not meet."
    )

    # Act 2: repetition and problem
    world.para()
    plant.memes["curiosity"] += 1
    plant.memes["repetition"] += 1
    world.say(
        f"{plant.id} leaned closer once, then once again, then once again once more; "
        f"it was curious, it was serious, and it peeped toward the tray and door."
    )
    world.say(
        f"{plant.id} sniffed the croissant and leaned so near, with leaves like little fans; "
        f"the warm sweet smell said, “Come this way,” and woke the plant’s soft plans."
    )
    plant.memes["curiosity"] += 1
    plant.memes["repetition"] += 1
    croissant.meters["crumbs"] += 1
    plant.memes["worry"] += 1
    butler.memes["worry"] += 1
    world.say(
        f"But the croissant was flaky, and flaky things can shed; a crumb or two was sure to fall "
        f"where polished leaves were fed."
    )

    # Act 3: gentle turn
    world.para()
    world.say(
        f"The butler saw the curious peeks, the little sniff-and-spin, "
        f"and smiled a calm, kind butter-smile that said, “Let’s choose a safer din.”"
    )
    butler.memes["patience"] += 1
    plant.memes["curiosity"] += 1
    world.say(
        f"“We can look, then have a book,” the butler said with cheer. "
        f“First we move the crumbly treat away, and then you may come near.”"
    )
    croissant.meters["crumbs"] = 0.0
    plant.meters["thirst"] += 1
    plant.meters["warmth"] += 1
    plant.memes["delight"] += 1
    butler.memes["pride"] += 1
    world.say(
        f"So the croissant went to a cloth-lined plate, and the plant got a little mist; "
        f"the leaves grew bright, the room felt light, and nothing got amiss."
    )
    world.say(
        f"{plant.id} watched the plate, then watched the spray, then watched the tray anew; "
        f"the same sweet sight came twice to life, and that was fun to do."
    )

    world.facts.update(
        plant=plant,
        butler=butler,
        croissant=croissant,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# Rhyming helpers and Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    plant = world.facts["plant"]
    return [
        f'Write a short rhyming story about a curious plant named {plant.id}, a butler, and a croissant.',
        f'Tell a child-friendly story where a plant keeps looking again and again at a croissant, and a butler helps.',
        f'Write a tiny rhyming tale with curiosity and repetition, ending with a gentle fix in {world.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    plant = world.facts["plant"]
    butler = world.facts["butler"]
    return [
        QAItem(
            question=f"Who was curious in the story?",
            answer=f"{plant.id} the little plant was curious. It kept peeking toward the croissant again and again.",
        ),
        QAItem(
            question=f"What did the butler keep on the tray?",
            answer=f"The butler kept a buttery croissant on the tray so it would be ready for tea.",
        ),
        QAItem(
            question=f"How did the butler solve the problem?",
            answer=f"The butler moved the crumbly croissant to a safer plate and gave the plant a little mist, so the leaves stayed neat.",
        ),
        QAItem(
            question=f"What repeating action did {plant.id} do?",
            answer=f"{plant.id} leaned closer, then did it again and again, showing repetition and curiosity.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a croissant?",
            answer="A croissant is a flaky, buttery pastry shaped like a crescent moon.",
        ),
        QAItem(
            question="Why do plants need water?",
            answer="Plants need water to stay healthy and keep their leaves and stems from drying out.",
        ),
        QAItem(
            question="What does a butler do?",
            answer="A butler is a helper who keeps things tidy and helps serve food or drinks.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_places() -> list[str]:
    return list(SETTINGS)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(valid_places())
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, name=name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
plant(P) :- plant_name(P).
butler(B) :- butler_name(B).
croissant(C) :- croissant_name(C).

curious(P) :- plant(P), curiosity(P, N), N > 0.
repeated(P) :- plant(P), repetition(P, N), N > 0.

crumb_risk(C) :- croissant(C), crumbs(C, N), N > 0.
problem(P, C) :- curious(P), repeated(P), crumb_risk(C).

fix(P, C) :- problem(P, C), moved_to_plate(C), misted(P).
resolved(P, C) :- fix(P, C).

#show curious/1.
#show repeated/1.
#show problem/2.
#show resolved/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("plant_name", "plant"))
    lines.append(asp.fact("butler_name", "butler"))
    lines.append(asp.fact("croissant_name", "croissant"))
    lines.append(asp.fact("curiosity", "plant", 2))
    lines.append(asp.fact("repetition", "plant", 2))
    lines.append(asp.fact("crumbs", "croissant", 1))
    lines.append(asp.fact("moved_to_plate", "croissant"))
    lines.append(asp.fact("misted", "plant"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show curious/1.\n#show repeated/1.\n#show problem/2.\n#show resolved/2."))
    atoms = sorted(set((s.name, len(s.arguments)) for s in model))
    want = [("curious", 1), ("problem", 2), ("repeated", 1), ("resolved", 2)]
    got = sorted(atoms)
    if got == want:
        print("OK: ASP twin matches the Python world shape.")
        return 0
    print("MISMATCH in ASP verification:")
    print("  got:", got)
    print("  want:", want)
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld about a curious plant, a butler, and a croissant.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--name", choices=NAMES)
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


CURATED = [
    StoryParams(place="sunroom", name="Pip"),
    StoryParams(place="kitchen", name="Milo"),
    StoryParams(place="tearoom", name="Nina"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show curious/1.\n#show repeated/1.\n#show problem/2.\n#show resolved/2."))
        print("ASP atoms:")
        for atom in model:
            print(atom)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.name} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
