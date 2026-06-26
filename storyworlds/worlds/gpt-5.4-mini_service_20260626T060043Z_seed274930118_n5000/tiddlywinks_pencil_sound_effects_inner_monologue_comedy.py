#!/usr/bin/env python3
"""
Story world: tiddlywinks, pencil, sound effects, inner monologue, comedy.

A tiny, constraint-checked domain about a child trying to play tiddlywinks
near a very important pencil, with bouncy sound effects and a lot of thinking
to themselves.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def __post_init__(self):
        if not self.meters:
            self.meters = {"mess": 0.0, "tension": 0.0, "joy": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "embarrassment": 0.0, "pride": 0.0, "resolve": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    soundy: bool = True
    clutter: bool = False
    afford_tiddlywinks: bool = True


@dataclass
class TiddlywinkSet:
    label: str = "tiddlywinks"
    phrase: str = "a little cup of tiddlywinks"
    kind: str = "tiddlywinks"
    sounds: list[str] = field(default_factory=lambda: ["plink!", "clack!", "boing!"])
    mess: str = "scattered"


@dataclass
class Pencil:
    label: str = "pencil"
    phrase: str = "a bright yellow pencil"
    kind: str = "pencil"
    brittle: bool = True


class World:
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

ROOMS = {
    "kitchen": Room(name="the kitchen", soundy=True, clutter=False, afford_tiddlywinks=True),
    "table": Room(name="the table", soundy=True, clutter=False, afford_tiddlywinks=True),
    "classroom": Room(name="the classroom", soundy=True, clutter=True, afford_tiddlywinks=True),
    "library": Room(name="the library", soundy=True, clutter=False, afford_tiddlywinks=False),
}

SET = TiddlywinkSet()
PENCIL = Pencil()

GIRL_NAMES = ["Mia", "Nora", "Lila", "Zoe", "Ava", "Iris"]
BOY_NAMES = ["Ben", "Leo", "Max", "Noah", "Eli", "Finn"]
TRAITS = ["silly", "curious", "bouncy", "cheeky", "careful", "chatty"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    room: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sound_fx(words: list[str]) -> str:
    return " ".join(words)


def build_line(world: World, text: str) -> None:
    world.say(text)


def inner_thought(hero: Entity, text: str) -> str:
    return f"({text})"


def reasonableness_check(params: StoryParams) -> None:
    if params.room not in ROOMS:
        raise StoryError("Unknown room.")
    room = ROOMS[params.room]
    if not room.afford_tiddlywinks:
        raise StoryError(f"(No story: {room.name} is too cramped or wrong for a tiddlywinks comedy.)")


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"mess": 0.0, "tension": 0.0, "joy": 0.0},
        memes={"worry": 0.0, "embarrassment": 0.0, "pride": 0.0, "resolve": 0.0},
    ))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    pencil = world.add(Entity(id="pencil", type="pencil", label="pencil", phrase=PENCIL.phrase, owner=hero.id, caretaker=parent.id))
    winks = world.add(Entity(id="winks", type="tiddlywinks", label="tiddlywinks", phrase=SET.phrase, owner=hero.id))

    # Beginning
    build_line(world, f"{hero.id} was a {params.trait} little {params.gender} who loved quiet games that went {sound_fx(['plink!', 'plink!', 'plonk!'])}.")
    build_line(world, f"{hero.id} also loved {pencil.label} because it could draw stars, ladders, and very serious-looking dragons.")
    build_line(world, f"One afternoon, {hero.id} set the {winks.label} beside {pencil.label} and grinned.")

    # Middle turn
    world.para()
    build_line(world, f"In {room.name}, the game started with a cheerful {sound_fx(['plip!', 'plink!', 'clack!'])}.")
    hero.meters["joy"] += 1
    hero.memes["pride"] += 1

    if room.clutter:
        hero.meters["mess"] += 1
        hero.memes["worry"] += 1

    build_line(world, f"{hero.id} wanted to flick the pieces fast, but the {pencil.label} was right there, looking far too important for chaos.")
    build_line(world, inner_thought(hero, "If I bonk the pencil, it will probably make a face. Pencils do not like making faces."))

    # Tension
    world.para()
    hero.meters["tension"] += 1
    build_line(world, f"Then came the big flick: {sound_fx(['boing!', 'ping!', 'tink!'])}")
    if room.soundy:
        build_line(world, f"The sound bounced around {room.name} like a rubber ball wearing shoes.")
    if room.clutter:
        build_line(world, f"One tiddlywink skittered, spun, and almost kissed the pencil.")
    else:
        build_line(world, f"One tiddlywink flew neatly past the pencil, which was a very lucky little pencil.")

    build_line(world, inner_thought(hero, "Please land anywhere except on the pencil. Anywhere. Even my elbow."))

    # Resolution
    world.para()
    hero.memes["resolve"] += 1
    hero.meters["tension"] = 0.0
    if room.clutter:
        build_line(world, f"{hero.id} took a breath, lined up the cup, and said, 'Slow and steady. No pencil drama today.'")
        build_line(world, f"Then {hero.id} moved the pencil to a safe corner and played with smaller flicks: {sound_fx(['plink!', 'plink!', 'plunk!'])}.")
    else:
        build_line(world, f"{hero.id} laughed, tucked the pencil a little farther away, and played again with careful fingers: {sound_fx(['plink!', 'clack!', 'plink!'])}.")

    hero.meters["joy"] += 1
    hero.memes["pride"] += 1

    build_line(world, f"At the end, the tiddlywinks were in a neat little pile, the pencil was safe, and {hero.id} was smiling like a person who had defeated a tiny disaster with one small breath.")
    build_line(world, f"{parent.label.capitalize()} looked over and shook {parent.pronoun('possessive')} head, laughing at the very serious game of {SET.label}.")

    world.facts = {
        "hero": hero,
        "parent": parent,
        "pencil": pencil,
        "winks": winks,
        "room": room,
        "params": params,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a funny story about {p.name} playing tiddlywinks near a pencil.",
        f"Tell a child-friendly comedy where a {p.gender} named {p.name} tries to keep a pencil safe while playing with tiddlywinks.",
        "Write a short humorous story with sound effects and inner monologue about a small game that could go slightly wrong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    room: Room = f["room"]
    pencil: Entity = f["pencil"]
    return [
        QAItem(
            question=f"What game was {hero.id} playing in {room.name}?",
            answer=f"{hero.id} was playing tiddlywinks, a tiny game with little pieces that go plink and clack.",
        ),
        QAItem(
            question=f"Why did {hero.id} move the {pencil.label} to a safe corner?",
            answer=f"{hero.id} moved the pencil so it would not get bumped during the tiddlywinks game. That kept the pencil safe and let the play stay funny instead of messy.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end of the story?",
            answer=f"{hero.id} felt happy and proud after keeping the pencil safe and finishing the game without a tiny disaster.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are tiddlywinks?",
            answer="Tiddlywinks is a game where you flick little pieces so they hop or bounce.",
        ),
        QAItem(
            question="What is a pencil for?",
            answer="A pencil is for drawing and writing.",
        ),
        QAItem(
            question="Why can sound effects make a story funny?",
            answer="Sound effects can make actions feel lively and silly, so the story sounds playful and cheerful.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thoughts, like the words they say in their head.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
room_ok(R) :- afford_tiddlywinks(R).
valid_story(R) :- room_ok(R).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.afford_tiddlywinks:
            lines.append(asp.fact("afford_tiddlywinks", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_rooms() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((rid,) for rid, room in ROOMS.items() if room.afford_tiddlywinks)
    cl = asp_valid_rooms()
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} rooms).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("python:", py)
    print("clingo:", cl)
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world: tiddlywinks and a pencil.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    room = args.room or rng.choice(list(ROOMS))
    reasonableness_check(StoryParams(room=room, name="x", gender="girl", parent="mother", trait="silly"))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(room=room, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    reasonableness_check(params)
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"room: {world.room.name}")
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
    StoryParams(room="kitchen", name="Mia", gender="girl", parent="mother", trait="bouncy"),
    StoryParams(room="table", name="Ben", gender="boy", parent="father", trait="cheeky"),
    StoryParams(room="classroom", name="Nora", gender="girl", parent="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        rooms = asp_valid_rooms()
        print(f"{len(rooms)} valid rooms:")
        for (rid,) in rooms:
            print(f"  {rid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
