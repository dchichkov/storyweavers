#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gasket_maid_guardian_sharing_magic_detective_story.py
===============================================================================================================================

A small detective-story world about a missing gasket, a maid, and a guardian
who must share clues and use a little magic to solve the case.

Premise used to build the world:
---
A careful guardian keeps a quiet house where tiny things sometimes go missing.
One evening, the kitchen tap starts to hiss because its round gasket has slipped
out of place. A maid notices the leak, and a young detective arrives to ask
questions. The guardian is worried, the maid has useful information, and both
must share what they know. A little magic helps reveal where the gasket rolled.

World model:
---
* meters: physical state, like leak_level, clue_strength, gasket_found
* memes: emotional/social state, like worry, trust, curiosity, relief

The story is driven by the state changes, not by a frozen paragraph.
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
# Core world entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"maid", "woman", "girl", "mother"}
        male = {"guardian", "man", "boy", "father", "detective"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the quiet house"
    rooms: list[str] = field(default_factory=lambda: ["kitchen", "hall", "laundry room"])


@dataclass
class Clue:
    kind: str
    room: str
    detail: str
    reveal: str


@dataclass
class StoryParams:
    place: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "house": Setting(place="the quiet house"),
    "manor": Setting(place="the old manor"),
    "flat": Setting(place="the narrow flat"),
}

MAID_NAMES = ["Mara", "Nina", "Etta", "June"]
GUARDIAN_NAMES = ["Rowan", "Silas", "Mina", "Otis"]
DETECTIVE_NAMES = ["Ivy", "Theo", "Lena", "Finn"]

CLUES = [
    Clue(kind="wet_footprint", room="kitchen", detail="a wet footprint by the sink", reveal="the leak started near the tap"),
    Clue(kind="thread", room="hall", detail="a loose thread caught on a doorknob", reveal="the maid had gone to fetch cloths"),
    Clue(kind="glint", room="laundry room", detail="a tiny silver glint under the basket", reveal="the gasket had rolled under the laundry basket"),
]

ASP_RULES = r"""
% The gasket is found when the detective shares clues and magic reveals the hiding place.
shares(maid). shares(guardian). shares(detective).
needs_magic(gasket).
case_solved :- shares(maid), shares(guardian), shares(detective), magic_used, gasket_found.
gasket_found :- clue(wet_footprint,kitchen), clue(thread,hall), clue(glint,laundry_room).
"""


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    guardian = world.add(Entity(
        id="Guardian", kind="character", type="guardian", label="the guardian",
        traits=["careful", "protective"],
        meters={"worry": 1.0, "trust": 0.0, "relief": 0.0},
        memes={"worry": 1.0, "trust": 0.0, "relief": 0.0},
    ))
    maid = world.add(Entity(
        id="Maid", kind="character", type="maid", label="the maid",
        traits=["tidy", "observant"],
        meters={"worry": 0.5, "trust": 0.0, "relief": 0.0},
        memes={"worry": 0.5, "trust": 0.0, "relief": 0.0},
    ))
    detective = world.add(Entity(
        id="Detective", kind="character", type="detective", label="the detective",
        traits=["curious", "calm"],
        meters={"curiosity": 1.0, "clue_strength": 0.0, "magic": 0.0},
        memes={"curiosity": 1.0, "confidence": 0.0},
    ))
    gasket = world.add(Entity(
        id="Gasket", kind="thing", type="gasket", label="the round gasket",
        phrase="a small round gasket from the kitchen tap",
        meters={"found": 0.0, "dry": 1.0},
        memes={"importance": 1.0},
    ))

    world.facts.update(setting=params.place, guardian=guardian, maid=maid, detective=detective, gasket=gasket)
    return world


def narrate_setup(world: World) -> None:
    guardian = world.get("Guardian")
    maid = world.get("Maid")
    detective = world.get("Detective")
    gasket = world.get("Gasket")

    world.say(f"In {world.setting.place}, {guardian.label} kept everything neat and quiet.")
    world.say(f"{maid.label.capitalize()} worked there too, and {detective.label} came by when the kitchen tap began to hiss.")
    world.say(f"The trouble was {gasket.label}, {gasket.phrase}, which had slipped out of place.")
    guardian.memes["worry"] += 1.0
    maid.memes["trust"] += 0.5
    detective.meters["curiosity"] += 0.5


def narrate_conflict(world: World) -> None:
    guardian = world.get("Guardian")
    maid = world.get("Maid")
    detective = world.get("Detective")

    world.para()
    world.say(f"{guardian.label.capitalize()} feared the leak would spread across the floor.")
    world.say(f"{maid.label.capitalize()} said she had seen something shiny near the sink, but the clue needed to be shared carefully.")
    world.say(f"{detective.label.capitalize()} asked both of them to tell the story in order, because little clues mattered.")
    guardian.memes["trust"] += 0.5
    maid.memes["trust"] += 0.5
    detective.meters["clue_strength"] += 1.0


def use_magic_and_share(world: World) -> None:
    guardian = world.get("Guardian")
    maid = world.get("Maid")
    detective = world.get("Detective")
    gasket = world.get("Gasket")

    world.para()
    world.say(f"{guardian.label.capitalize()} and {maid.label.capitalize()} shared what they knew: the wet floor, the silver glint, and the missing ring shape.")
    world.say(f"Then {detective.label} used a tiny bit of magic, and the air sparkled softly above the laundry basket.")
    detective.meters["magic"] += 1.0
    gasket.meters["found"] = 1.0
    guardian.meters["worry"] = 0.0
    maid.meters["worry"] = 0.0
    guardian.memes["worry"] = 0.0
    maid.memes["worry"] = 0.0
    guardian.memes["relief"] += 1.0
    maid.memes["relief"] += 1.0
    detective.memes["confidence"] += 1.0
    world.say(f"There, under the basket, was {gasket.label}. The clue trail had led straight to it.")


def narrate_resolution(world: World) -> None:
    guardian = world.get("Guardian")
    maid = world.get("Maid")
    detective = world.get("Detective")
    gasket = world.get("Gasket")

    world.para()
    world.say(f"{maid.label.capitalize()} fixed the tap, and the hissing stopped.")
    world.say(f"{guardian.label.capitalize()} smiled because the house was quiet again.")
    world.say(f"{detective.label.capitalize()} tucked {gasket.it()} safely in a cloth pouch so it would not get lost again.")
    world.say(f"By the end, everyone had shared a little more, and the small magic made the whole room feel brighter.")


def tell(params: StoryParams) -> World:
    world = build_world(params)
    narrate_setup(world)
    narrate_conflict(world)
    use_magic_and_share(world)
    narrate_resolution(world)

    world.facts["solved"] = True
    world.facts["magic_used"] = True
    world.facts["gasket_found"] = True
    return world


# ---------------------------------------------------------------------------
# Story and QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short detective story for young children about a missing gasket, a maid, and a guardian who share clues.',
        'Tell a gentle mystery where a maid and a guardian help a detective use a little magic to find a tiny gasket.',
        'Write a simple story in which sharing clues solves a small household mystery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    guardian = world.get("Guardian")
    maid = world.get("Maid")
    detective = world.get("Detective")
    gasket = world.get("Gasket")
    return [
        QAItem(
            question="What was missing from the kitchen tap?",
            answer="The missing thing was the round gasket from the kitchen tap.",
        ),
        QAItem(
            question="Who helped the detective solve the mystery?",
            answer=f"The maid and the guardian helped the detective by sharing clues about the leak.",
        ),
        QAItem(
            question="What did the detective use to find the gasket?",
            answer="The detective used a little magic, and it helped reveal the gasket under the laundry basket.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The tap was fixed, the leak stopped, and everyone felt relieved when the gasket was safely found.",
        ),
        QAItem(
            question=f"Where did {maid.label} see a clue?",
            answer="She saw a shiny clue near the sink and later helped share it with the detective.",
        ),
        QAItem(
            question=f"Why was {guardian.label} worried at the start?",
            answer="The guardian was worried because the kitchen tap was leaking and the gasket was missing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gasket?",
            answer="A gasket is a ring-shaped piece that helps seal a joint so water or air does not leak out.",
        ),
        QAItem(
            question="What does a maid do?",
            answer="A maid is a person who helps keep a house clean and tidy.",
        ),
        QAItem(
            question="What is a guardian?",
            answer="A guardian is someone who protects and watches over a person or place.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people have some information, help, or things instead of keeping it all to yourself.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special pretend power in stories that can make surprising things happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    lines.extend(world.trace)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Inline ASP twin for the reasonableness gate and story facts.

share(maid).
share(guardian).
share(detective).

mystery(gasket).
magic_needed(gasket).

solved :- share(maid), share(guardian), share(detective), magic_used, gasket_found.

#show solved/0.
#show share/1.
#show mystery/1.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("share", "maid"), asp.fact("share", "guardian"), asp.fact("share", "detective"),
             asp.fact("mystery", "gasket"), asp.fact("magic_used"), asp.fact("gasket_found")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/0."))
    atoms = {str(a) for a in model}
    if "solved" in atoms:
        print("OK: ASP twin confirms the mystery can be solved.")
        return 0
    print("MISMATCH: ASP twin did not confirm the mystery.")
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: gasket, maid, guardian, sharing, and magic.")
    ap.add_argument("--place", choices=SETTINGS.keys())
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    return StoryParams(place=place)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show share/1. #show mystery/1. #show solved/0."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
