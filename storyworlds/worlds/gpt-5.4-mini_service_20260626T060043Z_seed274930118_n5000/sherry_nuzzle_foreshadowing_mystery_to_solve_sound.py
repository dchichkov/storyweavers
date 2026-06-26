#!/usr/bin/env python3
"""
Small comedy storyworld: a cozy mystery with foreshadowing, sound effects,
and a gentle nuzzle that helps solve the puzzle.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "they" if self.plural else self.pronoun("subject")


@dataclass
class Room:
    name: str
    setting: str
    cozy: bool = True


@dataclass
class Clue:
    id: str
    label: str
    sound: str
    foreshadow: str
    solved_by: str


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        import copy
        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROOMS = {
    "porch": Room(name="the porch", setting="outdoors"),
    "kitchen": Room(name="the kitchen", setting="indoors"),
    "garden": Room(name="the garden", setting="outdoors"),
}

CHARACTER_NAMES = ["Sherry", "Milo", "Penny", "Bea", "Jasper"]
CHARACTER_TRAITS = ["curious", "silly", "bright-eyed", "bouncy", "cheerful"]

CLUES = {
    "jar": Clue(
        id="jar",
        label="jam jar",
        sound="clink-clink",
        foreshadow="A tiny sticky sparkle on the floor was the first clue.",
        solved_by="a gentle nuzzle under the bench",
    ),
    "bell": Clue(
        id="bell",
        label="little bell",
        sound="ding-ding",
        foreshadow="A soft ringing came from somewhere behind the chair.",
        solved_by="a nose bump near the ribbon",
    ),
    "shoe": Clue(
        id="shoe",
        label="shoe",
        sound="scritch-scritch",
        foreshadow="One lonely print looked like it had walked away by itself.",
        solved_by="a nuzzle beside the flower pot",
    ),
}

MYSTERIES = ["missing snack", "mystery sound", "vanished ribbon"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    room: str
    clue: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    clue = CLUES[params.clue]
    world = World(room)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="cat",
        label=params.name.lower(),
        traits=["little", "curious"],
        meters={"distance": 0.0},
        memes={"curiosity": 1.0, "joy": 1.0, "puzzle": 0.0, "relief": 0.0},
    ))
    friend = world.add(Entity(
        id="Nip",
        kind="character",
        type="dog",
        label="Nip",
        traits=["friendly"],
        meters={"distance": 0.0},
        memes={"curiosity": 0.5, "joy": 1.0},
    ))
    mystery = world.add(Entity(
        id="mystery",
        kind="thing",
        type="mystery",
        label=mysteries_phrase(params.clue),
        meters={"uncertainty": 1.0},
        memes={"suspense": 1.0},
    ))
    world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue.label,
        meters={"seen": 0.0},
        memes={"hint": 1.0},
    ))

    world.facts.update(hero=hero.id, friend=friend.id, mystery=mystery.label, clue=clue)
    return world


def mysteries_phrase(clue_id: str) -> str:
    return {
        "jar": "the missing jam",
        "bell": "the mystery ringing",
        "shoe": "the vanished shoe",
    }[clue_id]


def foreshadow_line(clue: Clue) -> str:
    return clue.foreshadow


def sound_effect(clue: Clue) -> str:
    return clue.sound


def solve_mystery(world: World) -> None:
    hero = world.get(world.facts["hero"])  # type: ignore[index]
    friend = world.get(world.facts["friend"])  # type: ignore[index]
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]

    hero.memes["puzzle"] += 1.0
    world.say(
        f"{hero.id} was sniffing around when {sound_effect(clue)} went the odd little sound."
    )
    world.say(foreshadow_line(clue))
    world.say(
        f"{friend.id} looked under the bench, but all {hero.pronoun('subject')} found was a crumb and a grin."
    )

    hero.meters["distance"] += 1.0
    friend.meters["distance"] += 1.0
    world.say(
        f"Then {hero.id} gave {friend.id} a tiny nuzzle, and {friend.id} wiggled toward the clue."
    )
    world.say(
        f"{clue.solved_by.capitalize()} revealed the answer: the {clue.label} had rolled away and made the noise."
    )
    hero.memes["joy"] += 1.0
    hero.memes["relief"] += 1.0
    hero.memes["puzzle"] = 0.0
    world.facts["solved"] = True
    world.facts["ending"] = f"The {clue.label} was found, and the mystery was not so scary after all."


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.get(world.facts["hero"])  # type: ignore[index]
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]

    world.say(
        f"On {world.room.name}, {hero.id} was a little curious cat who loved a good puzzle."
    )
    world.say(
        f"{hero.id} had heard one strange sound before: {sound_effect(clue)}."
    )
    world.say(
        f"So when the afternoon felt quiet and wobbly, {hero.id} knew a mystery was nearby."
    )
    world.para()
    solve_mystery(world)
    world.para()
    world.say(world.facts["ending"])  # type: ignore[index]
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    hero = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a funny little story about {hero} hearing {clue.sound} and solving a mystery with a nuzzle.",
        f"Tell a cozy comedy story on {world.room.name} that uses the words sherry and nuzzle.",
        f"Make a child-friendly mystery story with foreshadowing, a clue, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]  # type: ignore[assignment]
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"What did {hero} hear that made the mystery feel important?",
            answer=f"{hero} heard {clue.sound}, which was the odd little sound that hinted something was wrong.",
        ),
        QAItem(
            question="What clue foreshadowed the answer?",
            answer=clue.foreshadow,
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"It was solved when the friends used a gentle nuzzle and noticed that the {clue.label} had rolled away.",
        ),
    ]
    if world.facts.get("solved"):
        qa.append(QAItem(
            question="What changed by the end of the story?",
            answer="The strange worry turned into a happy laugh because the mystery was solved and everyone felt relieved.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small hint that gives readers a clue about what may happen later.",
        ),
        QAItem(
            question="What does a nuzzle mean?",
            answer="A nuzzle is a soft, friendly push with a nose or face, like a pet showing affection.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word written to suggest a noise, like clink-clink or ding-ding.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
room(porch).
room(kitchen).
room(garden).

clue(jar).
clue(bell).
clue(shoe).

foreshadow(jar, "A tiny sticky sparkle on the floor was the first clue.").
foreshadow(bell, "A soft ringing came from somewhere behind the chair.").
foreshadow(shoe, "One lonely print looked like it had walked away by itself.").

sound(jar, "clink-clink").
sound(bell, "ding-ding").
sound(shoe, "scritch-scritch").

solved(jar, "a gentle nuzzle under the bench").
solved(bell, "a nose bump near the ribbon").
solved(shoe, "a nuzzle beside the flower pot").

#show valid_story/2.
valid_story(Room, Clue) :- room(Room), clue(Clue).
"""


def asp_facts() -> str:
    import asp
    out = []
    for r in ROOMS:
        out.append(asp.fact("room", r))
    for c in CLUES:
        out.append(asp.fact("clue", c))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(r, c) for r in ROOMS for c in CLUES}
    ap = set(asp_valid_stories())
    if py == ap:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - ap))
    print("only in asp:", sorted(ap - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [(r, c) for r in ROOMS for c in CLUES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy comedy mystery storyworld.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
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
    room = args.room or rng.choice(list(ROOMS))
    clue = args.clue or rng.choice(list(CLUES))
    name = args.name or rng.choice(CHARACTER_NAMES)
    return StoryParams(room=room, clue=clue, name=name)


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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"room: {world.room.name}")
    for e in world.entities.values():
        lines.append(f"{e.id} ({e.kind}/{e.type}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for room in ROOMS:
            for clue in CLUES:
                params = StoryParams(room=room, clue=clue, name="Sherry")
                samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
