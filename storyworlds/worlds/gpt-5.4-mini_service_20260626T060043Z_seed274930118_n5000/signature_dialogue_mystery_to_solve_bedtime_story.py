#!/usr/bin/env python3
"""
storyworlds/worlds/signature_dialogue_mystery_to_solve_bedtime_story.py
========================================================================

A small bedtime-story world where a child finds a puzzling signature, asks
gentle questions, and solves a cozy mystery before sleep.

Premise:
- A child is getting ready for bed in a quiet room.
- They discover a mysterious signed note or keepsake.
- They and a caregiver follow soft clues and use dialogue to solve who left it.
- The ending image proves what changed: the mystery is solved, the worry is gone,
  and bedtime feels warm again.

This world is intentionally small and constraint-checked: only a few mystery
pairs are reasonable, and the ASP twin mirrors the same gate.

Seed inspiration:
- signature
- Dialogue
- Mystery to Solve
- Bedtime Story
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    kept_in: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    bedtime_place: str
    quiet: bool = True


@dataclass
class Mystery:
    id: str
    object_label: str
    object_phrase: str
    signer: str
    clue_kind: str
    clue_phrase: str
    ending_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    room: str
    mystery: str
    name: str
    gender: str
    caregiver: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room, mystery: Mystery) -> None:
        self.room = room
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

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

        w = World(self.room, self.mystery)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROOMS = {
    "nursery": Room(name="the nursery", bedtime_place="the nursery"),
    "attic_room": Room(name="the attic room", bedtime_place="the attic room"),
    "cozy_corner": Room(name="the cozy corner", bedtime_place="the cozy corner"),
}

MYSTERIES = {
    "bookmark": Mystery(
        id="bookmark",
        object_label="bookmark",
        object_phrase="a paper bookmark with a silver star",
        signer="Grandma",
        clue_kind="tea",
        clue_phrase="a tiny tea stain shaped like a crescent",
        ending_phrase="The bookmark was tucked back between the pages, safe and smooth.",
        tags={"paper", "book", "signature", "tea"},
    ),
    "pillow_note": Mystery(
        id="pillow_note",
        object_label="note",
        object_phrase="a folded note with curly writing",
        signer="Dad",
        clue_kind="ink",
        clue_phrase="a blue ink dot on the corner",
        ending_phrase="The note was slipped into a little box beside the pillow, where it could rest till morning.",
        tags={"paper", "note", "signature", "ink"},
    ),
    "music_card": Mystery(
        id="music_card",
        object_label="card",
        object_phrase="a little music card with a ribbon",
        signer="Big Sister",
        clue_kind="ribbon",
        clue_phrase="a ribbon fiber caught on the edge",
        ending_phrase="The music card stayed on the bedside table, ready to sing again tomorrow.",
        tags={"card", "music", "signature", "ribbon"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "June"]
BOY_NAMES = ["Theo", "Ben", "Max", "Leo", "Finn", "Owen"]
TRAITS = ["sleepy", "curious", "gentle", "brave", "quiet", "thoughtful"]


@dataclass
class CharacterPlan:
    signer_relation: str
    signer_phrase: str


# ---------------------------------------------------------------------------
# ASP / reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
room(r_nursery). room(r_attic_room). room(r_cozy_corner).

mystery(bookmark). mystery(pillow_note). mystery(music_card).

valid(r_nursery, bookmark).
valid(r_nursery, pillow_note).
valid(r_attic_room, pillow_note).
valid(r_attic_room, music_card).
valid(r_cozy_corner, bookmark).
valid(r_cozy_corner, music_card).

#show valid/2.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room", f"r_{rid}"))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for room in ROOMS:
        for mystery in MYSTERIES:
            if room == "nursery" and mystery in {"bookmark", "pillow_note"}:
                combos.append((room, mystery))
            elif room == "attic_room" and mystery in {"pillow_note", "music_card"}:
                combos.append((room, mystery))
            elif room == "cozy_corner" and mystery in {"bookmark", "music_card"}:
                combos.append((room, mystery))
    return combos


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
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
# Story construction
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime mystery storyworld with dialogue and a signature clue."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father", "grandmother", "grandfather"])
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
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid bedtime mystery matches the given options.)")
    room, mystery = rng.choice(sorted(combos))
    myst = MYSTERIES[mystery]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.caregiver or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(room=room, mystery=mystery, name=name, gender=gender, caregiver=caregiver, trait=trait)


def can_solve(world: World) -> bool:
    child = world.get("child")
    clue = world.get("clue")
    if world.mystery.id == "bookmark":
        return clue.meters.get("seen", 0) >= 1 and child.memes.get("curiosity", 0) >= 1
    if world.mystery.id == "pillow_note":
        return clue.meters.get("seen", 0) >= 1 and child.memes.get("worry", 0) < 2
    return clue.meters.get("seen", 0) >= 1


def generate_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    mystery = MYSTERIES[params.mystery]
    world = World(room, mystery)

    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    caregiver = world.add(Entity(id="caregiver", kind="character", type=params.caregiver, label=params.caregiver))
    clue = world.add(Entity(id="clue", kind="thing", type=mystery.object_label, label=mystery.object_label, phrase=mystery.object_phrase))

    child.memes["sleepy"] = 1
    child.memes["curiosity"] = 1
    child.memes["worry"] = 0
    clue.meters["hidden"] = 1

    world.say(f"{params.name} was a {params.trait} little {params.gender} getting ready for bed in {room.bedtime_place}.")
    world.say(f"{params.name} liked the soft lamp glow, the warm blanket, and the quiet talk before sleep.")
    world.para()

    world.say(f"Then {params.name} noticed something small near the pillow: {mystery.object_phrase}.")
    world.say(f"It had a strange signature on it, and that made the room feel full of mystery.")
    child.memes["worry"] += 1
    clue.meters["hidden"] = 0
    clue.meters["seen"] = 1
    world.para()

    world.say(f'"{Did you see this?" {params.name} whispered.')
    world.say(f'"I did," said {params.caregiver}. "Let us look for clues instead of guessing."')
    world.say(f'"But whose signature is it?" {params.name} asked.')
    world.say(f'"We can solve it together," said {params.caregiver}.')
    child.memes["curiosity"] += 1
    world.para()

    world.say(f"They looked closely and found {mystery.clue_phrase}.')
    world.say(f'"That clue matters," said {params.caregiver}. "{mystery.signer} has a habit of leaving {mystery.clue_kind} when {mystery.signer} writes notes."')
    if mystery.id == "pillow_note":
        world.say(f'"A blue ink dot means someone leaned on the page too soon," {params.name} said, peeking at the corner.')
    elif mystery.id == "bookmark":
        world.say(f'"Tea on paper usually means the note was written near a warm cup," {params.name} said in a tiny voice.')
    else:
        world.say(f'"A ribbon fiber could only come from a gift tied up with care," {params.name} said.')
    world.para()

    world.say(f'"Who do you think signed it?" asked {params.caregiver}.')
    world.say(f'"Maybe {mystery.signer}," {params.name} said, and the guess felt closer to right with every clue.')
    world.say(f'"Let us check one more thing," said {params.caregiver}, and they matched the clue to the person who would know the bedtime surprise.')
    world.say(f'Then the mystery opened like a book: {mystery.signer} had left a loving note just for {params.name}.')
    world.say(f'"{mystery.signer} signed it so you would know it was from someone who loves you," said {params.caregiver}.')
    world.para()

    child.memes["worry"] = 0
    child.memes["joy"] = 2
    world.say(f'{params.name} smiled, tucked the note carefully away, and said, "Now I know."')
    world.say(f'{mystery.ending_phrase}')
    world.say(f'The lamp grew softer, the room grew quieter, and {params.name} felt sleepy in a happy, solved sort of way.')

    world.facts.update(
        child=child,
        caregiver=caregiver,
        clue=clue,
        mystery=mystery,
        room=room,
        solved=can_solve(world),
        signer=mystery.signer,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle bedtime story where a child finds a mysterious signature and solves who left it.',
        f'Tell a cozy dialogue story in {f["room"].bedtime_place} about {f["child"].label} discovering {f["mystery"].object_phrase}.',
        f'Write a bedtime mystery for children where the clue {f["mystery"].clue_phrase} helps identify {f["mystery"].signer}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    mystery = f["mystery"]
    room = f["room"]
    return [
        QAItem(
            question=f"Where was {child.label} when the mysterious signature was found?",
            answer=f"{child.label} was in {room.bedtime_place}, getting ready for bed when the mystery appeared.",
        ),
        QAItem(
            question=f"What did {child.label} find near the pillow?",
            answer=f"{child.label} found {mystery.object_phrase}. It had a signature on it, so it felt like a little bedtime mystery.",
        ),
        QAItem(
            question=f"How did {child.label} and {caregiver.label} solve the mystery?",
            answer=f"They looked at the clue {mystery.clue_phrase} and talked about who would leave it. That led them to {mystery.signer}.",
        ),
        QAItem(
            question=f"What was the answer to the mystery?",
            answer=f"The signature belonged to {mystery.signer}, who had left the note or keepsake with love.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery = f["mystery"]
    out = [
        QAItem(
            question="What is a signature?",
            answer="A signature is a person's written name or mark that shows who made or approved something.",
        ),
        QAItem(
            question="Why do people look for clues in a mystery?",
            answer="People look for clues so they can figure out the answer instead of guessing wildly.",
        ),
    ]
    if "tea" in mystery.tags:
        out.append(QAItem(question="Why can tea leave a stain?", answer="Tea has color in it, and if it spills on paper, it can leave a brown mark."))
    if "ink" in mystery.tags:
        out.append(QAItem(question="Why is ink useful for writing?", answer="Ink makes dark letters and names that are easy to read on paper."))
    if "ribbon" in mystery.tags:
        out.append(QAItem(question="What is a ribbon for?", answer="A ribbon can tie up a gift or decorate something in a pretty way."))
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {e.type:12} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def explain_rejection() -> str:
    return "(No story: that room and mystery pairing does not have a gentle clue trail.)"


CURATED = [
    StoryParams(room="nursery", mystery="pillow_note", name="Mia", gender="girl", caregiver="mother", trait="curious"),
    StoryParams(room="cozy_corner", mystery="bookmark", name="Theo", gender="boy", caregiver="grandfather", trait="thoughtful"),
    StoryParams(room="attic_room", mystery="music_card", name="Nora", gender="girl", caregiver="father", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible room/mystery combos:\n")
        for room, mystery in combos:
            print(f"  {room:11} {mystery}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
