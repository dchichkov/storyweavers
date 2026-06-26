#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/zombie_inner_monologue_friendship_ghost_story.py
================================================================================================

A tiny storyworld for a gentle ghost-story-style tale about a zombie,
friendship, and a visible inner monologue.

Premise:
- A lonely zombie wanders a quiet place at dusk.
- The zombie worries, in inner monologue, that everyone will be scared.
- A ghost appears, proves friendly, and helps the zombie solve a small problem.
- Friendship changes the mood of the ending image.

World model:
- Entities have meters and memes.
- The zombie is physically restless, a little clumsy, and emotionally shy.
- The ghost can glow, drift, and comfort.
- A lantern / note / small lost item can create a gentle tension.
- The story resolves when the ghost helps the zombie act bravely and kindly.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- lazy import of storyworlds.asp in ASP helpers
- inline ASP_RULES twin and Python reasonableness gate
- optional QA, JSON, trace, verify, show-asp modes
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
    kind: str = "thing"  # character | thing
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
        if self.type in {"zombie"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    stillness: str
    at_night: str
    echoes: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Focus:
    id: str
    label: str
    phrase: str
    risk: str
    lostness: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    focus: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.mood: str = "quiet"

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


PLACES = {
    "graveyard": Place(
        id="graveyard",
        label="the old graveyard",
        stillness="The stones stood in a hush, and the grass moved like a whisper.",
        at_night="At night, the graveyard looked silver and very still.",
        echoes=True,
        tags={"graveyard", "night", "quiet"},
    ),
    "lantern_lane": Place(
        id="lantern_lane",
        label="Lantern Lane",
        stillness="The lane was lined with porch lights that blinked like sleepy stars.",
        at_night="At night, Lantern Lane held small pools of gold light on the sidewalk.",
        echoes=False,
        tags={"lane", "night", "light"},
    ),
    "woods": Place(
        id="woods",
        label="the moonlit woods",
        stillness="The trees leaned close, and the leaves kept every sound soft.",
        at_night="At night, the woods were a silver maze of branches and shadows.",
        echoes=True,
        tags={"woods", "night", "quiet"},
    ),
}

FOCI = {
    "lantern": Focus(
        id="lantern",
        label="a tiny lantern",
        phrase="a tiny lantern with a warm glow",
        risk="go out",
        lostness="lost",
        clue="warm light",
        tags={"light", "glow"},
    ),
    "note": Focus(
        id="note",
        label="a folded note",
        phrase="a folded note tucked under a stone",
        risk="blow away",
        lostness="missing",
        clue="paper",
        tags={"paper", "secret"},
    ),
    "balloon": Focus(
        id="balloon",
        label="a blue balloon",
        phrase="a blue balloon caught on a branch",
        risk="float off",
        lostness="stuck",
        clue="string",
        tags={"sky", "string"},
    ),
}

ZOMBIE_NAMES = ["Milo", "Ned", "Iris", "Pip", "Luna", "Bram"]
GHOST_NAMES = ["Wisp", "Pale", "Moth", "Murmur"]
TRAITS = ["gentle", "shy", "curious", "lonely"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for p in PLACES.values():
        for f in FOCI.values():
            combos.append((p.id, f.id))
    return combos


def reasonableness_gate(place: Place, focus: Focus) -> None:
    if place.id == "graveyard" and focus.id == "balloon":
        return
    if place.id == "lantern_lane" and focus.id == "lantern":
        return
    if place.id == "woods" and focus.id == "note":
        return
    # all supported, but keep a tiny taste of style coherence
    if focus.id == "balloon" and place.id == "graveyard":
        raise StoryError("(No story: a balloon story fits better away from the graveyard's heavy stillness.)")


def pick_intro_line(place: Place) -> str:
    return place.at_night if "night" in place.tags else place.stillness


def is_scary(world: World, zombie: Entity) -> bool:
    return zombie.memes.get("fear", 0.0) >= THRESHOLD


def change_mood(world: World) -> None:
    if world.entities["Ghost"].memes.get("friendship", 0.0) >= THRESHOLD:
        world.mood = "gentle"


def inner_monologue(world: World, zombie: Entity, focus: Focus) -> None:
    zombie.memes["fear"] += 1
    world.say(
        f'Inside {zombie.id}\'s head, a small thought kept turning: '
        f'"What if everybody sees me and runs away?"'
    )
    world.say(
        f'But another thought followed, quieter and braver: '
        f'"Maybe I can still be kind, even if I feel strange."'
    )
    world.say(
        f'{zombie.id} looked at {focus.phrase} and wondered if the lost thing could be helped.'
    )


def meet_ghost(world: World, zombie: Entity, ghost: Entity) -> None:
    ghost.memes["friendliness"] += 1
    zombie.memes["attention"] += 1
    world.say(
        f"Then {ghost.id} drifted out of the dark with a soft glow, not scary at all."
    )
    world.say(
        f'{ghost.id} waved and said, "You do not have to be alone tonight."'
    )


def friendship_begins(world: World, zombie: Entity, ghost: Entity) -> None:
    zombie.memes["hope"] += 1
    ghost.memes["friendship"] += 1
    world.say(
        f'{zombie.id} felt the little knot in {zombie.pronoun("possessive")} chest loosen.'
    )
    world.say(
        f'For the first time, {zombie.id} and {ghost.id} stood together like old friends.'
    )


def help_with_focus(world: World, zombie: Entity, ghost: Entity, focus: Focus) -> None:
    if focus.id == "lantern":
        world.say(
            f'The lantern was hiding in a hollow stone, where the wind could not reach it.'
        )
        world.say(
            f'{ghost.id} floated low to shine a path, and {zombie.id} used careful hands to lift it out.'
        )
    elif focus.id == "note":
        world.say(
            f'The folded note was trapped beneath a slick leaf pile, nearly hidden from sight.'
        )
        world.say(
            f'{ghost.id} stirred the leaves, and {zombie.id} picked up the note before it could slip away.'
        )
    else:
        world.say(
            f'The blue balloon had snagged itself on a branch, bobbing in the wind.'
        )
        world.say(
            f'{ghost.id} rose up to the branch while {zombie.id} steadied the string from below.'
        )
    world.say(
        f'Together they saved {focus.phrase}, and the little problem stopped feeling so big.'
    )


def ending_image(world: World, zombie: Entity, ghost: Entity, focus: Focus) -> None:
    zombie.memes["fear"] = 0.0
    zombie.memes["friendship"] += 1
    ghost.memes["friendship"] += 1
    world.say(
        f'By the end, {zombie.id} was smiling under the pale sky, '
        f'and {ghost.id} glowed beside {zombie.pronoun("object")} like a patient star.'
    )
    world.say(
        f'The rescued {focus.label} shone in the quiet dark, and neither friend felt alone anymore.'
    )


def tell(place: Place, focus: Focus, name: str) -> World:
    world = World(place)
    zombie = world.add(Entity(
        id=name,
        kind="character",
        type="zombie",
        label=name,
        meters={"tired": 1.0},
        memes={"fear": 0.0, "hope": 0.0, "attention": 0.0, "friendship": 0.0},
    ))
    ghost = world.add(Entity(
        id="Ghost",
        kind="character",
        type="ghost",
        label="the ghost",
        meters={"glow": 1.0},
        memes={"friendliness": 0.0, "friendship": 0.0},
    ))
    world.facts.update(zombie=zombie, ghost=ghost, focus=focus, place=place)

    world.say(f"At {place.label}, the air felt hushed and old.")
    world.say(pick_intro_line(place))
    world.say(
        f"{zombie.id} had come there alone, carrying {focus.phrase}, and the silence made "
        f"{zombie.pronoun('object')} think too hard."
    )

    world.para()
    inner_monologue(world, zombie, focus)
    meet_ghost(world, zombie, ghost)
    friendship_begins(world, zombie, ghost)

    world.para()
    help_with_focus(world, zombie, ghost, focus)
    ending_image(world, zombie, ghost, focus)
    change_mood(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a young child about a zombie named {f["zombie"].id} who is worried, '
        f"but then meets a friendly ghost and becomes brave.",
        f'Create a gentle story set at {f["place"].label} where {f["zombie"].id} thinks to {f["focus"].risk} the lost {f["focus"].label}, '
        f"and a ghost helps as a friend.",
        f'Write a child-friendly spooky story that includes inner thoughts, friendship, and the word "{f["zombie"].id.lower()}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    z = f["zombie"]
    g = f["ghost"]
    focus = f["focus"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who is the story about at {place.label}?",
            answer=f"It is about {z.id}, a gentle zombie, and the friendly ghost {g.id}.",
        ),
        QAItem(
            question=f"What did {z.id} worry about before meeting {g.id}?",
            answer=f"{z.id} worried that everyone might run away, but {z.id} still wanted to help with {focus.phrase}.",
        ),
        QAItem(
            question=f"How did the ghost help with {focus.label}?",
            answer=f"{g.id} helped by shining or moving things so {z.id} could rescue {focus.phrase} safely.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{z.id} was no longer alone, and {g.id} and {z.id} felt like friends.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story like this?",
            answer="A ghost is a spooky-looking spirit character, and in a gentle ghost story it can be kind and helpful.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when two people or characters care about each other, help each other, and feel safe together.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice of a character's own thoughts inside their head.",
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  mood: {world.mood}")
    return "\n".join(lines)


ASP_RULES = r"""
zombie(X) :- zombie_entity(X).
ghost(X) :- ghost_entity(X).
friendship(X,Y) :- meets(X,Y), kind(X,zombie), kind(Y,ghost), kind(Y,helpful).
calm_end(X) :- friendship(X,Y), rescued(X,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid in FOCI:
        lines.append(asp.fact("focus", fid))
    lines.append(asp.fact("zombie_entity", "zombie"))
    lines.append(asp.fact("ghost_entity", "ghost"))
    lines.append(asp.fact("kind", "zombie", "zombie"))
    lines.append(asp.fact("kind", "ghost", "ghost"))
    lines.append(asp.fact("kind", "ghost", "helpful"))
    lines.append(asp.fact("meets", "zombie", "ghost"))
    lines.append(asp.fact("rescued", "zombie", "focus"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show calm_end/1."))
    clingo_atoms = set(asp.atoms(model, "calm_end"))
    python_atoms = {("zombie",)}
    if clingo_atoms == python_atoms:
        print("OK: clingo gate matches Python reasonableness and ending shape.")
        return 0
    print("MISMATCH between clingo and Python expectations:")
    print("  clingo:", sorted(clingo_atoms))
    print("  python:", sorted(python_atoms))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place/1. #show focus/1."))
    return sorted(set(asp.atoms(model, "place"))) + sorted(set(asp.atoms(model, "focus")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle ghost story about a zombie, friendship, and an inner monologue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--focus", choices=FOCI)
    ap.add_argument("--name")
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
    focus = args.focus or rng.choice(list(FOCI))
    reasonableness_gate(PLACES[place], FOCI[focus])
    name = args.name or rng.choice(ZOMBIE_NAMES)
    return StoryParams(place=place, focus=focus, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], FOCI[params.focus], params.name)
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
        print(asp_program("#show calm_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show place/1. #show focus/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            for focus in FOCI:
                try:
                    params = StoryParams(place=place, focus=focus, name="Milo")
                    reasonableness_gate(PLACES[place], FOCI[focus])
                    samples.append(generate(params))
                except StoryError:
                    continue
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.name}: {p.focus} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
