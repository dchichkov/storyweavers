#!/usr/bin/env python3
"""
A tiny ghost-story world with a bad ending.

Seed tale:
A little night drummer found an old cymbal in the attic. Every time the cymbal
rang, the room went colder and the candlelight went boob-dim. The drummer
wanted to play one more song, even after the ghost in the corner warned that
music would wake the sleeping house. The drummer hit the cymbal again anyway.
The ghost grew tall in the dark, the candle went out, and the house stayed
silent.

This script turns that premise into a small simulated story domain where state
changes drive the prose: sound, light, fear, and haunting all matter.
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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    dimness: float = 0.0
    hush: float = 0.0


@dataclass
class Instrument:
    id: str
    label: str
    sound: str
    kind: str
    booms: set[str] = field(default_factory=set)
    dims: set[str] = field(default_factory=set)
    cursed: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
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
        other = World(copy.deepcopy(self.place))
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


def _r_boom(world: World) -> list[str]:
    out = []
    drummer = world.entities.get("child")
    cymbal = world.entities.get("cymbal")
    if not drummer or not cymbal:
        return out
    if drummer.meters.get("hit", 0.0) < THRESHOLD:
        return out
    sig = ("boom",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.place.dimness += 1.0
    world.place.hush += 1.0
    out.append("The room grew colder and quieter.")
    return out


def _r_boo_b_dim(world: World) -> list[str]:
    out = []
    if world.place.dimness < THRESHOLD:
        return out
    sig = ("boob-dim",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lantern = world.entities.get("lantern")
    if lantern:
        lantern.meters["light"] = max(0.0, lantern.meters.get("light", 1.0) - 1.0)
    out.append("The lantern went boob-dim.")
    return out


def _r_wake_ghost(world: World) -> list[str]:
    out = []
    if world.place.dimness < THRESHOLD:
        return out
    ghost = world.entities.get("ghost")
    if not ghost:
        return out
    sig = ("wake",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["awake"] = 1.0
    ghost.memes["loom"] = 1.0
    out.append("Something pale opened its eyes in the corner.")
    return out


def _r_bad_ending(world: World) -> list[str]:
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    if not ghost or not child:
        return []
    if ghost.memes.get("loom", 0.0) < THRESHOLD:
        return []
    sig = ("bad_end",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = 2.0
    child.memes["quiet"] = 2.0
    return ["__bad_end__"]


RULES = [_r_boom, _r_boo_b_dim, _r_wake_ghost, _r_bad_ending]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            got = rule(world)
            if got:
                changed = True
                out.extend([s for s in got if s != "__bad_end__"])
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "attic"
    name: str = "Milo"
    instrument: str = "cymbal"
    ending: str = "bad"


PLACES = {
    "attic": Place(id="attic", label="the attic"),
    "hall": Place(id="hall", label="the hall"),
    "cellar": Place(id="cellar", label="the cellar"),
}

INSTRUMENTS = {
    "cymbal": Instrument(
        id="cymbal",
        label="an old cymbal",
        sound="CLANG",
        kind="cymbal",
        booms={"sound"},
        dims={"light"},
        cursed=True,
    ),
}

NAMES = ["Milo", "Nina", "Toby", "Lina", "June", "Arlo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--instrument", choices=INSTRUMENTS)
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
    place = args.place or rng.choice(list(PLACES))
    instrument = args.instrument or "cymbal"
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, name=name, instrument=instrument, seed=None)


def predict(world: World, actor: Entity) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["hit"] = 1.0
    propagate(sim, narrate=False)
    return {
        "dark": sim.place.dimness >= THRESHOLD,
        "ghost_awake": sim.entities["ghost"].memes.get("awake", 0.0) >= THRESHOLD,
    }


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    child = world.add(Entity(id="child", kind="character", type="boy", label=params.name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost"))
    cymbal = world.add(Entity(
        id="cymbal",
        type="instrument",
        label="cymbal",
        phrase="an old cymbal",
        owner=child.id,
    ))
    lantern = world.add(Entity(id="lantern", type="thing", label="lantern"))
    lantern.meters["light"] = 1.0

    world.say(f"{params.name} found {INSTRUMENTS[params.instrument].label} in {world.place.label}.")
    world.say("The attic smelled like dust and wet wood, and the lantern made a small warm dot.")
    world.para()
    world.say(f"{params.name} loved the big ringing sound of the cymbal, even though it made the shadows jump.")
    world.say("In that old room, the air felt still, as if the house was holding its breath.")
    world.para()

    child.meters["hit"] = 1.0
    world.say(f"{params.name} hit the cymbal once, and the note rang out like a sharp silver bell.")
    world.say(f"{params.name} heard the strange word boob-dim in the flicker of the lantern.")
    propagate(world, narrate=True)
    world.para()

    pred = predict(world, child)
    world.facts["predicted_dark"] = pred["dark"]
    world.facts["predicted_ghost_awake"] = pred["ghost_awake"]

    world.say("The ghost in the corner lifted its head.")
    world.say(f"{params.name} should have stopped, but {params.name} wanted one more loud ring.")
    child.meters["hit"] = 2.0
    propagate(world, narrate=True)

    if world.entities["ghost"].memes.get("loom", 0.0) >= THRESHOLD:
        world.say("At the end, the lantern was nearly gone, the cymbal was cold in small hands, and the ghost stood where the light used to be.")
        world.say(f"{params.name} did not sleep that night.")
    world.facts.update(child=child, ghost=ghost, cymbal=cymbal, lantern=lantern, place=world.place)
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a child using the word "cymbal" and the phrase "boob-dim".',
        f"Tell a spooky story where {f['child'].label} finds a cymbal in {f['place'].label} and makes the light go dim.",
        "Write a simple haunted-house story with a bad ending, a ringing instrument, and a disappearing light.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    return [
        QAItem(
            question="What did the child find in the attic?",
            answer="The child found an old cymbal in the attic.",
        ),
        QAItem(
            question="Why did the room feel scarier after the cymbal rang?",
            answer="The cymbal made the room colder and darker, and the lantern went boob-dim.",
        ),
        QAItem(
            question="What happened at the end of the story?",
            answer=f"The lantern was almost out, the ghost stood in the dark, and {child.label} did not sleep that night.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cymbal?",
            answer="A cymbal is a metal music plate that makes a ringing crash when it is hit.",
        ),
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright, like a light that is getting weak.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a spooky tale about a ghost, a mystery, or a scary place.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    parts = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        parts.append(f"{e.id}: {e.type} {' '.join(bits)}")
    parts.append(f"place: {world.place.label} dimness={world.place.dimness} hush={world.place.hush}")
    parts.append(f"fired: {sorted(world.fired)}")
    return "\n".join(parts)


ASP_RULES = r"""
dark :- dimmed.
ghost_awake :- dark.
bad_ending :- ghost_awake.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("instrument", "cymbal"),
            asp.fact("word", "boob-dim"),
            asp.fact("place", "attic"),
            asp.fact("theme", "ghost_story"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show dark/0. #show ghost_awake/0. #show bad_ending/0."))
    atoms = {s.name for s in model}
    expected = {"dark", "ghost_awake", "bad_ending"}
    if atoms == expected:
        print("OK: ASP twin matches the bad-ending ghost-story gate.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


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
    StoryParams(place="attic", name="Milo", instrument="cymbal"),
    StoryParams(place="cellar", name="Nina", instrument="cymbal"),
    StoryParams(place="hall", name="Arlo", instrument="cymbal"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible ghost-story setup: cymbal + boob-dim + bad ending.")
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name} in {p.place} with {p.instrument}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
