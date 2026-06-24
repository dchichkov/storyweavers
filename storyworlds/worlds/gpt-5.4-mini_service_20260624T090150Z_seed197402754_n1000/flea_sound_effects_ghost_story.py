#!/usr/bin/env python3
"""
storyworlds/worlds/flea_sound_effects_ghost_story.py
=====================================================

A small ghost-story world with a tiny flea, big spooky hopes, and the sound
effects that change the mood of the night.

Seed tale:
---
A little ghost lived in an old house and loved to make spooky noises in the dark.
One night, a flea hopped onto the ghost's sheet. Every time the ghost tried to say
"BOO," the flea made tiny zip-zip sounds and scratchy squeaks. The ghost got upset
because the sounds made the scare feel silly. Then the ghost listened more closely,
realized the flea's little sounds were funny instead of frightening, and used them
as part of a new show. The house ended up full of soft laughter, little squeaks,
and one proud ghost with a new friend.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SFX = {"whooo", "boo", "zip", "skritch", "tap", "squeak", "clink"}


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
        if self.type in {"ghost"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    rooms: tuple[str, ...] = ("the attic", "the hallway", "the nursery")


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    sound: str
    helps: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.room: str = setting.rooms[0]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.room = self.room
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_itch(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    flea = world.get("flea")
    if ghost.meters.get("itch", 0) < THRESHOLD:
        return out
    sig = ("itch",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["irritated"] = ghost.memes.get("irritated", 0) + 1
    flea.meters["bounce"] = flea.meters.get("bounce", 0) + 1
    out.append("The ghost shivered, because the little itch would not go away.")
    out.append("The flea kept hopping on the ghost's sheet.")
    return out


def _r_sfx(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    flea = world.get("flea")
    if ghost.meters.get("spook", 0) < THRESHOLD:
        return out
    if flea.meters.get("bounce", 0) < THRESHOLD:
        return out
    sig = ("sfx",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["pride"] = ghost.memes.get("pride", 0) + 1
    ghost.memes["embarrassed"] = ghost.memes.get("embarrassed", 0) + 1
    out.append('The ghost tried to say "BOO," but the room answered with tiny zip-zip sounds.')
    out.append("A scratchy squeak slipped out too, and the scare sounded silly.")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    flea = world.get("flea")
    if ghost.memes.get("embarrassed", 0) < THRESHOLD:
        return out
    sig = ("laugh",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["joy"] = ghost.memes.get("joy", 0) + 1
    ghost.memes["lonely"] = max(0, ghost.memes.get("lonely", 0) - 1)
    flea.memes["playful"] = flea.memes.get("playful", 0) + 1
    out.append("Then the ghost listened closely and heard how funny the tiny sounds really were.")
    out.append("The ghost began to laugh, and the flea did a happy little bounce-bounce.")
    return out


CAUSAL_RULES = [Rule("itch", _r_itch), Rule("sfx", _r_sfx), Rule("laugh", _r_laugh)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def _perform_spook(world: World, ghost: Entity) -> None:
    ghost.meters["spook"] = ghost.meters.get("spook", 0) + 1
    ghost.memes["confidence"] = ghost.memes.get("confidence", 0) + 1
    world.say(f"At {world.room}, {ghost.id} floated up and tried to make the darkest, biggest scare of the night.")
    propagate(world, narrate=True)


def _notice_flea(world: World, ghost: Entity, flea: Entity) -> None:
    ghost.meters["itch"] = ghost.meters.get("itch", 0) + 1
    flea.meters["bounce"] = flea.meters.get("bounce", 0) + 1
    world.say("But something tickled under the ghost's sheet.")
    world.say("A tiny flea had arrived, and every hop made a little zip sound.")
    propagate(world, narrate=True)


def _respond(world: World, ghost: Entity, flea: Entity) -> None:
    if ghost.memes.get("embarrassed", 0) >= THRESHOLD:
        world.say("The ghost felt the cheeks of its face cool and ghostly, because the big scare had turned into a joke.")
    if ghost.memes.get("joy", 0) >= THRESHOLD:
        world.say("So the ghost flapped the sheet like a curtain and let the flea take the loudest part.")
        world.say("Together they made a new spooky show with boo, zip-zip, and a happy squeak.")


def tell(name: str = "Milo", trait: str = "shy") -> World:
    world = World(Setting())
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="little ghost"))
    flea = world.add(Entity(id="flea", kind="character", type="flea", label="tiny flea"))
    ghost.memes["lonely"] = 1
    ghost.memes["confidence"] = 0
    flea.memes["playful"] = 1

    world.say(f"In the old house, a {trait} little ghost named {name} lived in the dark rooms and loved to say spooky things.")
    world.say(f"{name} liked the sound of {name}'s own {SFX.pop()} when the halls were quiet.")  # one-time spice
    SFX.add("whooo")
    world.para()
    _perform_spook(world, ghost)
    world.para()
    _notice_flea(world, ghost, flea)
    world.para()
    _respond(world, ghost, flea)

    world.facts.update(ghost=ghost, flea=flea, name=name, trait=trait)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle ghost story for a young child that includes a flea and tiny sound effects.',
        f"Tell a story about a {f['trait']} ghost named {f['name']} who wants to sound spooky but hears a flea making zip-zip noises.",
        "Write a child-friendly ghost story where a tiny mistake changes a scary moment into a funny one.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    ghost = f["ghost"]
    flea = f["flea"]
    return [
        QAItem(
            question=f"Who lived in the old house and wanted to sound spooky?",
            answer=f"A {f['trait']} little ghost named {f['name']} lived there and wanted to make a spooky sound show.",
        ),
        QAItem(
            question="What tiny creature made the ghost's scare sound silly?",
            answer="A flea did it. Its little hops made zip-zip sounds and a scratchy squeak.",
        ),
        QAItem(
            question="How did the ghost feel after the spooky sound turned funny?",
            answer="The ghost felt less lonely and more cheerful, because the silly sounds became a fun part of the show.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flea?",
            answer="A flea is a very tiny insect that hops fast and can make a person or animal feel itchy.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises like whoosh, tap, squeak, or boo that help make a story feel alive.",
        ),
        QAItem(
            question="Why do people sometimes laugh at silly sounds?",
            answer="People laugh at silly sounds because they can surprise them and sound funny instead of serious.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    lines.append(f"  room: {world.room}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    name: str = "Milo"
    trait: str = "shy"
    seed: Optional[int] = None


ASP_RULES = r"""
ghost_confident(G) :- ghost(G), spooks(G), not embarrassed(G).
sound_effect(S) :- flea(F), makes(F,S).
funny_show(G) :- ghost(G), sound_effect(_), joyful(G).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("ghost", "ghost"),
        asp.fact("flea", "flea"),
        asp.fact("spooks", "ghost"),
        asp.fact("makes", "flea", "zip"),
        asp.fact("makes", "flea", "squeak"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_story_shape() -> bool:
    return True


def asp_verify() -> int:
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost story world with a flea and sound effects.")
    ap.add_argument("--name")
    ap.add_argument("--trait")
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
    return StoryParams(
        name=args.name or rng.choice(["Milo", "Nina", "Pip", "Tessa"]),
        trait=args.trait or rng.choice(["shy", "brave", "curious", "gentle"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.trait)
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
        print(asp_program("#show ghost_confident/1. #show sound_effect/1. #show funny_show/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(name=n, trait=t)) for n, t in [("Milo", "shy"), ("Pip", "curious"), ("Nina", "gentle")]]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
