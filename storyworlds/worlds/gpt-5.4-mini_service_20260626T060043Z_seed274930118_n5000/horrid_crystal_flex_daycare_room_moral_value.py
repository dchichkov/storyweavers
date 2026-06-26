#!/usr/bin/env python3
"""
A small storyworld set in a daycare room with a Tall Tale flavor.

Premise:
- A child finds a horrid-looking crystal.
- A showy flex creates trouble.
- The group solves a mystery in the daycare room.
- The ending teaches a moral value: honesty and helping.

The world is intentionally tiny, state-driven, and constraint-checked.
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

PLACE = "the daycare room"

NAMES = [
    "Milo", "Tessa", "Junie", "Arlo", "Pippa", "Nico", "Mira", "Benny",
    "Luna", "Theo", "Rosa", "Otis",
]

ADULTS = ["teacher", "helper"]
TRAITS = ["bold", "curious", "cheerful", "sly", "lively", "kind", "stubborn"]

MOODS = ["proud", "worried", "embarrassed", "brave", "grumpy", "hopeful"]

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
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


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    name: str
    trait: str
    adult: str
    crystal_kind: str
    flex_kind: str
    mystery_kind: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

CRYSTALS = {
    "horrid": {
        "label": "a horrid crystal",
        "phrase": "a horrid crystal with a crooked shine",
        "effect": "made everyone squint",
        "clue": "it left glittery dust on the shelf",
    },
    "bright": {
        "label": "a bright crystal",
        "phrase": "a bright crystal that flashed like a little moon",
        "effect": "caught everybody's eye",
        "clue": "it sparkled under the lamp",
    },
    "sleepy": {
        "label": "a sleepy crystal",
        "phrase": "a sleepy crystal that looked dusty and old",
        "effect": "hid in plain sight",
        "clue": "it was tucked behind a block tower",
    },
}

FLEXES = {
    "muscle": {
        "label": "a flexed bicep pose",
        "action": "flex his arms",
        "result": "shook the block tower",
        "risk": "knocked things loose",
    },
    "hat": {
        "label": "a big showy hat tilt",
        "action": "tip a fancy hat",
        "result": "sent the hat rolling",
        "risk": "hid the clue",
    },
    "dance": {
        "label": "a fancy dance flex",
        "action": "strut and spin",
        "result": "spun the rug",
        "risk": "scrambled the search",
    },
}

MYSTERIES = {
    "missing block": {
        "problem": "a favorite block went missing",
        "question": "Where did the favorite block go?",
        "answer": "It was under the rug, hidden by the spinning and the shuffle.",
    },
    "broken chalk": {
        "problem": "the chalk broke in two",
        "question": "Who broke the chalk?",
        "answer": "Nobody meant to; the block tower tipped it over during the flex.",
    },
    "sticky spoon": {
        "problem": "the snack spoon was sticky",
        "question": "Why was the spoon sticky?",
        "answer": "It had landed in a little puddle of juice near the table.",
    },
}

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(crystal_kind: str, flex_kind: str, mystery_kind: str) -> bool:
    if crystal_kind == "horrid" and mystery_kind == "missing block":
        return True
    if crystal_kind == "bright" and mystery_kind == "broken chalk":
        return True
    if crystal_kind == "sleepy" and mystery_kind == "sticky spoon":
        return True
    return False


def explain_rejection(crystal_kind: str, flex_kind: str, mystery_kind: str) -> str:
    return (
        f"(No story: the {crystal_kind} crystal, {flex_kind} flex, and "
        f"{mystery_kind} mystery do not make a believable daycare-room puzzle.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if not valid_combo(params.crystal_kind, params.flex_kind, params.mystery_kind):
        raise StoryError(explain_rejection(params.crystal_kind, params.flex_kind, params.mystery_kind))

    world = World(place=PLACE)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        label=params.name,
        memes={"curiosity": 1.0, "mood": 0.0},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        label=params.adult,
        memes={"calm": 1.0, "moral": 0.0},
    ))
    crystal_cfg = CRYSTALS[params.crystal_kind]
    flex_cfg = FLEXES[params.flex_kind]
    mystery_cfg = MYSTERIES[params.mystery_kind]

    crystal = world.add(Entity(
        id="crystal",
        label=crystal_cfg["label"],
        phrase=crystal_cfg["phrase"],
        owner=params.name,
        carried_by=params.name,
        meters={"shine": 1.0},
    ))
    toy = world.add(Entity(
        id="toy",
        label=flex_cfg["label"],
        phrase=flex_cfg["label"],
        owner=params.name,
        meters={"wobble": 0.0},
    ))
    clue = world.add(Entity(
        id="clue",
        label="the clue",
        phrase=mystery_cfg["problem"],
        meters={"hidden": 1.0},
    ))

    # Act 1: setup
    world.say(
        f"{params.name} was a {params.trait} little child in {PLACE}, "
        f"where the blocks were stacked high and the crayons lived in a tin cup."
    )
    world.say(
        f"One day, {params.name} found {crystal_cfg['phrase']} in a toy basket, "
        f"and {crystal_cfg['effect']}."
    )

    world.para()

    # Act 2: mystery and tension
    world.say(
        f"Right then, {params.name} tried to {flex_cfg['action']} in a great tall-tale way, "
        f"and {flex_cfg['result']}."
    )
    toy.meters["wobble"] = 1.0
    clue.meters["hidden"] = 0.0 if params.flex_kind == "hat" else 1.0
    child.memes["mood"] = 1.0
    adult.memes["calm"] = 0.5

    world.say(
        f"Suddenly, {mystery_cfg['problem']}, and the whole daycare room got as hushed as a mouse in a mitten."
    )
    world.say(
        f"{params.adult.capitalize()} frowned and said the room would need a careful look, not just a loud pose."
    )

    # Act 3: solve
    world.para()
    child.memes["curiosity"] = 2.0
    adult.memes["moral"] = 1.0

    world.say(
        f"{params.name} stopped to think, then told {params.adult} the truth about the crystal and the flex."
    )
    world.say(
        f"Together they searched under the rug, behind the blocks, and beside the paper crowns."
    )

    if params.mystery_kind == "missing block":
        world.say(
            f"There, under the rug, they found the missing block, tucked away where the spinning feet had sent it."
        )
    elif params.mystery_kind == "broken chalk":
        world.say(
            f"There they found the broken chalk, and at last the story made sense: the wobbling blocks had done it."
        )
    else:
        world.say(
            f"There they found the sticky spoon, shining with juice, and the mystery was plain as porridge."
        )

    world.say(
        f"{params.name} put the {crystal_cfg['label']} back where it belonged and helped tidy the mess."
    )
    world.say(
        f"{params.adult.capitalize()} smiled and said, 'A true giant tells the truth and helps fix trouble.'"
    )
    world.say(
        f"So the daycare room settled down again, with the crystal safe, the clue found, and {params.name} feeling mighty proud."
    )

    world.facts.update(
        child=child,
        adult=adult,
        crystal=crystal,
        toy=toy,
        clue=clue,
        params=params,
        crystal_cfg=crystal_cfg,
        flex_cfg=flex_cfg,
        mystery_cfg=mystery_cfg,
        moral="honesty and helping",
        solved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a Tall Tale for a child in {PLACE} that uses the words "{p.crystal_kind}", "{p.flex_kind}", and "{p.mystery_kind}".',
        f"Tell a short moral story where {p.name} finds {f['crystal_cfg']['label']} and helps solve a mystery.",
        "Write a daycare-room story with a ridiculous pose, a hidden clue, and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    crystal_cfg = f["crystal_cfg"]
    flex_cfg = f["flex_cfg"]
    mystery_cfg = f["mystery_cfg"]
    return [
        QAItem(
            question=f"What did {p.name} find in the daycare room?",
            answer=f"{p.name} found {crystal_cfg['label']} in the toy basket.",
        ),
        QAItem(
            question=f"What did {p.name} do that made the room extra noisy?",
            answer=f"{p.name} tried to {flex_cfg['action']} and that made the room wobble and shuffle.",
        ),
        QAItem(
            question=f"What mystery did they solve?",
            answer=f"They solved the mystery of {mystery_cfg['problem']}.",
        ),
        QAItem(
            question="What moral value did the adult teach?",
            answer="The adult taught honesty and helping, because telling the truth and fixing trouble made everything better.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    return [
        QAItem(
            question="What is a daycare room?",
            answer="A daycare room is a room where children play, learn, rest, and take care of toys together.",
        ),
        QAItem(
            question="What does a crystal usually look like?",
            answer="A crystal usually looks shiny, clear, or sparkly, like a little piece of treasure.",
        ),
        QAItem(
            question="What does it mean to flex?",
            answer="To flex means to show off a muscle or make a showy pose, usually to look strong or fancy.",
        ),
        QAItem(
            question="Why is telling the truth important?",
            answer="Telling the truth helps people solve problems, trust each other, and fix mistakes more easily.",
        ),
        QAItem(
            question=f"Why did the story need {p.adult}?",
            answer="The adult helped keep the room calm, guided the search, and reminded everyone to do the right thing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the chosen crystal, flex, and mystery fit together.
valid_story(Crystal, Flex, Mystery) :- crystal(Crystal), flex(Flex), mystery(Mystery),
    valid_pair(Crystal, Mystery).

% Inline compatibility twin of the Python reasonableness gate.
valid_pair(horrid, "missing block").
valid_pair(bright, "broken chalk").
valid_pair(sleepy, "sticky spoon").
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for c in CRYSTALS:
        lines.append(asp.fact("crystal", c))
    for f in FLEXES:
        lines.append(asp.fact("flex", f))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {
        (c, f, m)
        for c in CRYSTALS
        for f in FLEXES
        for m in MYSTERIES
        if valid_combo(c, f, m)
    }
    asp_set = set(asp_valid_stories())
    if asp_set == python_set:
        print(f"OK: clingo gate matches valid_combo() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and python validity:")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale daycare-room storyworld with a mystery to solve and a moral value."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--crystal-kind", choices=CRYSTALS)
    ap.add_argument("--flex-kind", choices=FLEXES)
    ap.add_argument("--mystery-kind", choices=MYSTERIES)
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
    crystal_kind = args.crystal_kind or rng.choice(list(CRYSTALS))
    flex_kind = args.flex_kind or rng.choice(list(FLEXES))
    mystery_kind = args.mystery_kind or rng.choice(list(MYSTERIES))
    if args.crystal_kind and args.flex_kind and args.mystery_kind:
        if not valid_combo(crystal_kind, flex_kind, mystery_kind):
            raise StoryError(explain_rejection(crystal_kind, flex_kind, mystery_kind))
    elif not valid_combo(crystal_kind, flex_kind, mystery_kind):
        # Try a few times to find a compatible combination.
        combos = [
            (c, f, m)
            for c in CRYSTALS
            for f in FLEXES
            for m in MYSTERIES
            if valid_combo(c, f, m)
        ]
        if args.crystal_kind:
            combos = [t for t in combos if t[0] == args.crystal_kind]
        if args.flex_kind:
            combos = [t for t in combos if t[1] == args.flex_kind]
        if args.mystery_kind:
            combos = [t for t in combos if t[2] == args.mystery_kind]
        if not combos:
            raise StoryError("(No valid combination matches the given options.)")
        crystal_kind, flex_kind, mystery_kind = rng.choice(sorted(combos))

    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    adult = args.adult or rng.choice(ADULTS)
    return StoryParams(
        name=name,
        trait=trait,
        adult=adult,
        crystal_kind=crystal_kind,
        flex_kind=flex_kind,
        mystery_kind=mystery_kind,
    )


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
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id}: {' '.join(bits)}")
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
    StoryParams(name="Milo", trait="curious", adult="teacher", crystal_kind="horrid", flex_kind="muscle", mystery_kind="missing block"),
    StoryParams(name="Tessa", trait="bold", adult="helper", crystal_kind="bright", flex_kind="dance", mystery_kind="broken chalk"),
    StoryParams(name="Junie", trait="kind", adult="teacher", crystal_kind="sleepy", flex_kind="hat", mystery_kind="sticky spoon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
