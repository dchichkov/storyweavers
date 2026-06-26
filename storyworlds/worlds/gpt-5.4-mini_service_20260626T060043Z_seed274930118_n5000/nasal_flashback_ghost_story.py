#!/usr/bin/env python3
"""
storyworlds/worlds/nasal_flashback_ghost_story.py
==================================================

A small ghost-story world with a gentle flashback shape.

Premise:
- A child feels a nasal tickle in a quiet house at dusk.
- A small ghost makes the child remember a comforting scarf from the past.
- The tension is not danger, but worry: the child cannot stop sneezing and feels alone.
- The turn is a flashback that reveals the scarf's warm smell and the old trick for easing a stuffy nose.
- The resolution is a calm, ghostly helper moment that leaves the child soothed and safe.

The story stays child-facing and soft:
- No horror violence.
- No cursed endings.
- The ghost is a helper who appears through memory and moonlight.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    quiet: bool = True
    moonlit: bool = False


@dataclass
class StoryParams:
    room: str
    child_name: str
    child_type: str
    ghost_name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_events: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _tickle(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters.get("nasal_tickle", 0.0) < THRESHOLD:
        return out
    sig = ("tickle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    out.append("The tickle in the child's nose made the quiet room feel bigger.")
    return out


def _sneeze(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters.get("nasal_tickle", 0.0) < THRESHOLD:
        return out
    sig = ("sneeze",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["embarrassed"] = child.memes.get("embarrassed", 0.0) + 1.0
    out.append("A tiny sneeze burst out, and the child blinked at the sudden sound.")
    return out


def _comfort(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    scarf = world.get("scarf")
    if child.memes.get("memory", 0.0) < THRESHOLD:
        return out
    sig = ("comfort",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["nasal_tickle"] = max(0.0, child.meters.get("nasal_tickle", 0.0) - 1.0)
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0
    scarf.meters["warmth"] = scarf.meters.get("warmth", 0.0) + 1.0
    out.append("The remembered scarf seemed to bring a softer, warmer breath to the room.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_tickle, _sneeze, _comfort):
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_type,
        label=params.child_name,
        traits=["little", "sleepy"],
        meters={"nasal_tickle": 1.0},
        memes={"worry": 0.0, "hope": 0.0, "memory": 0.0, "calm": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label=params.ghost_name,
        traits=["gentle", "moonlit"],
        meters={"glow": 1.0},
        memes={"kindness": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="adult",
        label=params.helper_name,
        traits=["careful", "soft"],
        memes={"concern": 0.0, "love": 1.0},
    ))
    scarf = world.add(Entity(
        id="scarf",
        type="scarf",
        label="old scarf",
        phrase="a soft old scarf with a warm smell",
        owner=child.id,
        caretaker=helper.id,
        meters={"warmth": 0.0},
    ))

    # Act 1: setup
    world.say(f"{child.label} sat in {room.name} when the evening turned quiet and blue.")
    world.say(f"{child.pronoun().capitalize()} had a tickly nose, and every breath felt a little nasal.")
    world.say(f"At the window, {ghost.label} hovered like a pale ribbon of moonlight.")
    world.say(f"{helper.label} kept watch nearby with {scarf.label} folded in a small, careful bundle.")

    # Act 2: worry + flashback
    world.para()
    world.say(f"{child.label} sniffled and rubbed {child.pronoun('possessive')} nose.")
    world.say(f"{ghost.label} did not scare {child.pronoun('object')}; {ghost.pronoun()} only whispered, 'Remember.'")
    child.memes["memory"] += 1.0
    world.say(
        f"That word opened a flashback: once, on a cold morning, {helper.label} had wrapped "
        f"{child.pronoun('object')} in {scarf.label} and said it could help a stuffy nose feel less lonely."
    )
    propagate(world, narrate=True)

    # Act 3: resolution
    world.para()
    helper.memes["concern"] += 1.0
    world.say(f"{helper.label} smiled, unwrapped {scarf.label}, and held it close so it could warm up again.")
    world.say(f"{ghost.label} drifted closer, as if happy to help the memory stay bright.")
    world.say(f"{child.label} breathed in the scarf's soft smell and let out a tiny, relieved sigh.")
    child.meters["nasal_tickle"] = 0.0
    child.memes["hope"] += 1.0
    child.memes["calm"] += 1.0
    world.say(
        f"By the end, the tickle was gone, the room felt gentle, and {child.label} could smile "
        f"under the moonlight while {ghost.label} kept watch."
    )

    world.facts.update(
        child=child,
        ghost=ghost,
        helper=helper,
        scarf=scarf,
        room=room,
    )
    return world


ROOMS = {
    "bedroom": Room(name="the bedroom", quiet=True, moonlit=True),
    "hall": Room(name="the hall", quiet=True, moonlit=False),
    "attic": Room(name="the attic", quiet=True, moonlit=True),
}

NAMES = ["Mina", "Noah", "Lia", "Eli", "Ruby", "Theo"]
GHOST_NAMES = ["Murmur", "Willow", "Pale Bell", "Cloud"]
HELPER_NAMES = ["Mom", "Dad", "Aunt June", "Grandpa"]

CURATED = [
    StoryParams(room="bedroom", child_name="Mina", child_type="girl", ghost_name="Willow", helper_name="Mom"),
    StoryParams(room="hall", child_name="Theo", child_type="boy", ghost_name="Murmur", helper_name="Dad"),
    StoryParams(room="attic", child_name="Ruby", child_type="girl", ghost_name="Cloud", helper_name="Aunt June"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle ghost story for a small child with a stuffy nose, and include a flashback to a comforting memory.",
        f"Tell a quiet story in {f['room'].name} where {f['child'].label} feels nasal, then remembers how {f['helper'].label} helped before.",
        f"Write a child-facing ghost story where {f['ghost'].label} appears like moonlight and helps {f['child'].label} calm down.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    ghost: Entity = f["ghost"]
    helper: Entity = f["helper"]
    scarf: Entity = f["scarf"]
    room: Room = f["room"]
    return [
        QAItem(
            question=f"Who had the tickly nose in {room.name}?",
            answer=f"{child.label} had the tickly nose, and the story says it felt nasal and uncomfortable.",
        ),
        QAItem(
            question=f"What did {ghost.label} help {child.label} remember?",
            answer=f"{ghost.label} helped {child.label} remember the old scarf and the kind moment when {helper.label} wrapped it around {child.pronoun('object')}.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The nasal tickle went away, the room felt gentle, and {child.label} finished the story feeling calm under the moonlight.",
        ),
        QAItem(
            question=f"Why was the scarf important?",
            answer=f"The scarf mattered because it was part of the flashback and helped {child.label} feel better when the nose tickle was bothering {child.pronoun('object')}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a gentle story?",
            answer="In a gentle story, a ghost can be a soft, floating helper from memory or moonlight, not something scary.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story briefly shows something from the past so the reader understands a character's memory.",
        ),
        QAItem(
            question="What does nasal mean?",
            answer="Nasal means related to the nose, like a tickly nose or a voice that sounds a bit stuffed up.",
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.quiet:
            lines.append(asp.fact("quiet", rid))
        if room.moonlit:
            lines.append(asp.fact("moonlit", rid))
    lines.append(asp.fact("symptom", "nasal"))
    lines.append(asp.fact("device", "flashback"))
    lines.append(asp.fact("figure", "ghost"))
    lines.append(asp.fact("aid", "scarf"))
    lines.append(asp.fact("aid_helps", "scarf", "nasal"))
    lines.append(asp.fact("aid_supports", "flashback", "memory"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(R, nasal, flashback, ghost) :- room(R), quiet(R), moonlit(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("bedroom", "nasal", "flashback", "ghost"),
          ("hall", "nasal", "flashback", "ghost"),
          ("attic", "nasal", "flashback", "ghost")}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(cl)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    if py - cl:
        print(" only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with nasal worry and a flashback.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--name")
    ap.add_argument("--ghost")
    ap.add_argument("--helper")
    ap.add_argument("--child-type", choices=["girl", "boy"])
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
    child_name = args.name or rng.choice(NAMES)
    child_type = args.child_type or rng.choice(["girl", "boy"])
    ghost_name = args.ghost or rng.choice(GHOST_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(room=room, child_name=child_name, child_type=child_type,
                       ghost_name=ghost_name, helper_name=helper_name)


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 compatible stories:\n")
        for row in asp_valid():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
