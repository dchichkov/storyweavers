#!/usr/bin/env python3
"""
A small whodunit story world: someone enters a tum-dim place, feels lonely,
notices clues, and solves a gentle mystery through inner monologue and
foreshadowing.
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

ASP_RULES = r"""
% Facts describe rooms, suspects, clues, and tools.

suspicious(Person) :- clue_on(Person, _, _).
can_solve(Detective) :- knows(Detective, clue), has(Detective, lamp), hears(Detective, whisper).
mystery_resolved(Detective) :- can_solve(Detective), enters(Detective, Room), dim(Room).

% A lonely detective can still reason clearly, and the inner monologue helps.
steady(Detective) :- lonely(Detective), thinks(Detective).

% The story is valid when the detective enters a tum-dim place, notices clues,
% and resolves the mystery without external help.
valid_story(Room, Detective) :- enters(Detective, Room), dim(Room), lonely(Detective), mystery_resolved(Detective), steady(Detective).
#show valid_story/2.
"""

ROOMS = {
    "attic": {"label": "the tum-dim attic", "dim": True, "places": {"box", "lamp", "footprint"}},
    "hall": {"label": "the tum-dim hall", "dim": True, "places": {"key", "coat", "footprint"}},
    "study": {"label": "the tum-dim study", "dim": True, "places": {"letter", "chair", "ink"}},
    "kitchen": {"label": "the tum-dim kitchen", "dim": True, "places": {"spoon", "crumb", "note"}},
}

SUSPECTS = {
    "cat": "the cat",
    "maid": "the maid",
    "uncle": "the uncle",
    "neighbor": "the neighbor",
}

CLUES = {
    "footprint": "a small footprint",
    "ink": "a dark ink smear",
    "crumb": "a trail of crumbs",
    "note": "a half-torn note",
    "key": "a bent key",
    "lamp": "a dusty lamp",
    "box": "a wooden box",
    "coat": "a dropped coat",
    "letter": "a sealed letter",
    "spoon": "a silver spoon",
    "chair": "a tipped chair",
}

TOOLS = {
    "lamp": "a pocket lamp",
    "notebook": "a little notebook",
    "magnifier": "a round magnifier",
}

NAMES = ["Mina", "Theo", "Iris", "Noah", "Lena", "Ari", "June", "Eli"]
TRAITS = ["quiet", "careful", "sharp", "patient", "brave"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def say(self, case: str = "subject") -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    room: str
    detective: str
    suspect: str
    clue: str
    seed: Optional[int] = None


@dataclass
class World:
    room: str
    detective: Entity
    suspect: Entity
    clue: Entity
    tool: Entity
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def note(self, line: str) -> None:
        self.trace.append(line)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world with inner monologue and foreshadowing.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
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
    room = args.room or rng.choice(sorted(ROOMS))
    clue = args.clue or rng.choice(sorted(ROOMS[room]["places"]))
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    name = args.name or rng.choice(NAMES)
    if clue not in ROOMS[room]["places"]:
        raise StoryError("That clue does not belong in this room, so the mystery would not feel grounded.")
    return StoryParams(room=room, detective=name, suspect=suspect, clue=clue)


def asp_facts() -> str:
    import asp
    lines = []
    for room, cfg in ROOMS.items():
        if cfg["dim"]:
            lines.append(asp.fact("dim", room))
        for thing in sorted(cfg["places"]):
            lines.append(asp.fact("in_room", thing, room))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    ax = set(asp_valid_stories())
    if py == ax:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - ax))
    print("  only in clingo:", sorted(ax - py))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for room in ROOMS:
        for clue in ROOMS[room]["places"]:
            combos.append((room, clue))
    return combos


def generate_world(params: StoryParams) -> World:
    detective = Entity(params.detective, kind="character", label=params.detective, meters={"lonely": 1.0}, memes={"curiosity": 1.0})
    suspect = Entity(params.suspect, kind="character", label=SUSPECTS[params.suspect], meters={"nervous": 0.5})
    clue = Entity(params.clue, kind="thing", label=CLUES[params.clue], meters={"noticed": 1.0})
    tool = Entity("lamp", kind="thing", label=TOOLS["lamp"], meters={"light": 1.0})
    world = World(room=params.room, detective=detective, suspect=suspect, clue=clue, tool=tool)
    world.facts.update(params=params, room=params.room, detective=detective, suspect=suspect, clue=clue)
    return world


def tell_story(world: World) -> str:
    room_label = ROOMS[world.room]["label"]
    det = world.detective.label
    suspect = world.suspect.label
    clue = world.clue.label
    if clue == "a wooden box":
        reveal = "the box had been moved only to hide a key"
    elif clue == "a half-torn note":
        reveal = "the note pointed straight to the study door"
    elif clue == "a small footprint":
        reveal = "the footprint matched the muddy edge by the hall"
    elif clue == "a dark ink smear":
        reveal = "the ink came from a spilled pen on the chair"
    elif clue == "a trail of crumbs":
        reveal = "the crumbs led to the kitchen drawer"
    elif clue == "a bent key":
        reveal = "the key opened the box in the attic"
    elif clue == "a dusty lamp":
        reveal = "the lamp still worked, and its beam showed fresh marks"
    elif clue == "a dropped coat":
        reveal = "the coat hid a note in its pocket"
    elif clue == "a sealed letter":
        reveal = "the letter named the true helper"
    elif clue == "a silver spoon":
        reveal = "the spoon had the suspect's initials on it"
    else:
        reveal = "the clue made the room's secret easy to see"

    world.note("entered room")
    world.note("inner monologue")
    world.note("foreshadowing")
    world.note("reveal")

    story = (
        f"{det} entered {room_label} and paused in the hush. "
        f"The place felt lonely, as if even the dust was holding its breath. "
        f'Inside {det}\'s mind, a small inner monologue began: "Do not rush. '
        f'People who hurry miss what the room is trying to say." '
        f'On the table sat {clue}, and {det} had the uneasy feeling it had been waiting there for a reason. '
        f"Even before the answer came, there was foreshadowing in the way {suspect} kept glancing at the door. "
        f'{det} lifted {world.tool.label} and studied the room. '
        f'Little by little, the clue and the silence fit together: {reveal}. '
        f"In the end, the lonely room was not lonely at all, because the mystery had finally been named."
    )
    world.facts["story_reveal"] = reveal
    return story


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a whodunit story where {world.facts["params"].detective} enters {ROOMS[world.room]["label"]} and solves a small mystery.',
        f'Write a short mystery for children that uses the words "enter", "tum-dim", and "lonely", with inner monologue and foreshadowing.',
        f'Tell a gentle detective story where a lonely child notices {world.clue.label} and figures out what happened.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Where did {p.detective} enter at the start of the story?",
            answer=f'{p.detective} entered {ROOMS[p.room]["label"]} at the start, and the room felt lonely and quiet.',
        ),
        QAItem(
            question=f"What clue did {p.detective} notice in the room?",
            answer=f'{p.detective} noticed {world.clue.label}, which helped turn the mystery from puzzling to clear.',
        ),
        QAItem(
            question=f"What did the inner monologue help {p.detective} do?",
            answer=f'The inner monologue helped {p.detective} slow down, think carefully, and connect the clues without guessing too fast.',
        ),
        QAItem(
            question=f"How did foreshadowing appear in the story?",
            answer=f'Foreshadowing appeared when {world.suspect.label} kept glancing at the door, hinting that the room had a secret.',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when a room is dim?",
            answer="A dim room is not very bright, so you may need a lamp or careful eyes to see details clearly.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the voice of thoughts inside a character's mind, like quiet thinking words.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints something important may happen later in the story.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"room={world.room}")
    lines.append(f"detective={world.detective.label} meters={world.detective.meters} memes={world.detective.memes}")
    lines.append(f"suspect={world.suspect.label} meters={world.suspect.meters} memes={world.suspect.memes}")
    lines.append(f"clue={world.clue.label} meters={world.clue.meters}")
    lines.append(f"tool={world.tool.label} meters={world.tool.meters}")
    lines.append(f"trace={world.trace}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    world = generate_world(params)
    story = tell_story(world)
    return StorySample(
        params=params,
        story=story,
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


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(room="attic", detective="Mina", suspect="cat", clue="box"),
            StoryParams(room="hall", detective="Theo", suspect="maid", clue="footprint"),
            StoryParams(room="study", detective="Iris", suspect="uncle", clue="letter"),
            StoryParams(room="kitchen", detective="Lena", suspect="neighbor", clue="crumb"),
        ]
        for p in curated:
            samples.append(generate(p))
        return samples

    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(args.n * 50, 50):
        seed = base_seed + i
        i += 1
        rng = random.Random(seed)
        try:
            params = resolve_params(args, rng)
        except StoryError as err:
            print(err)
            return []
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        for room, detective in combos:
            print(room, detective)
        return

    samples = build_samples(args)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
