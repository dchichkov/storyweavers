#!/usr/bin/env python3
"""
A small slice-of-life story world about a vampire, a husk, and a careful
deduction that leads through suspense, conflict, and a little magic.

The domain is deliberately tiny: one child-facing mystery at a cozy place, a
husk that went missing, and a vampire friend who helps solve it by noticing
clues instead of scaring anyone.
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
    kind: str
    label: str
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "child":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "vampire":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label


@dataclass
class Place:
    name: str
    detail: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
# Content registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    child: str
    vampire: str
    husk: str
    magic: str
    seed: Optional[int] = None


PLACES = {
    "garden": Place(name="the garden", detail="The garden was small and tidy, with a fence, a bench, and a sunny path."),
    "kitchen": Place(name="the kitchen", detail="The kitchen was warm, with a low table, a bowl of fruit, and a sleepy window."),
    "porch": Place(name="the porch", detail="The porch was quiet, with shoes by the door and a little basket on the step."),
}

CHILDREN = ["Mina", "Tess", "Nora", "Piper", "Lena", "Ivy"]
VAMPIRES = ["Ves", "Otto", "Bram", "Silas", "Ren"]
HUSKS = [
    ("corn husk", "a dry corn husk"),
    ("leaf husk", "a crinkly leaf husk"),
    ("paper husk", "a thin paper husk"),
]
MAGIC = [
    ("moon thread", "moon thread"),
    ("spark dust", "spark dust"),
    ("warm charm", "warm charm"),
]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _a(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


# ---------------------------------------------------------------------------
# Reasoning and causality
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    child = world.add(Entity(id="child", kind="child", label=params.child))
    vampire = world.add(Entity(id="vampire", kind="vampire", label=params.vampire))
    husk = world.add(Entity(id="husk", kind="object", label=params.husk, phrase=f"a small {params.husk}"))
    magic = world.add(Entity(id="magic", kind="object", label=params.magic, phrase=params.magic))

    world.facts.update(child=child, vampire=vampire, husk=husk, magic=magic, params=params)

    # State: the husk is missing from a familiar spot, creating suspense.
    husk.meters["missing"] = 1
    child.memes["curious"] = 1
    vampire.memes["watchful"] = 1
    vampire.memes["gentle"] = 1
    return world


def deduce_world(world: World) -> str:
    child = world.get("child")
    vampire = world.get("vampire")
    husk = world.get("husk")
    magic = world.get("magic")

    # A tiny deduction engine: clues imply where the husk is hiding.
    clue_spot = {
        "garden": "under the bench",
        "kitchen": "behind the fruit bowl",
        "porch": "inside the basket",
    }[world.place.name.removeprefix("the ")]
    world.facts["clue_spot"] = clue_spot

    world.say(f"{child.label} found a missing {husk.label} and looked around {world.place.name}.")
    world.say(world.place.detail)
    world.say(f"{vampire.label} noticed one clue at a time, because {vampire.pronoun('subject')} liked careful deduction better than guesses.")
    world.say(f"That made the morning feel a little suspenseful, like a tiny mystery hiding in plain sight.")

    world.para()
    world.say(f"{child.label} pointed at the clue and asked if the {husk.label} had floated away or been carried off.")
    world.say(f"{vampire.label} shook {vampire.pronoun('possessive')} head. \"It is probably {clue_spot},\" {vampire.pronoun('subject')} said.")
    world.say(f"{vampire.label} used a little {magic.label} to lift the cloth corner and peek, without breaking anything.")

    world.para()
    husk.carried_by = "child"
    world.facts["found"] = True
    world.say(f"Sure enough, the {husk.label} was there, exactly where the clues had said it would be.")
    world.say(f"{child.label} laughed in relief, and the suspense melted into a calm, happy afternoon.")
    world.say(f"Before long, {child.label} carried the {husk.label} home, and {vampire.label} smiled like a friend who had solved the nicest kind of puzzle.")
    return world.render()


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a gentle slice-of-life story about a vampire named {p.vampire} helping a child named {p.child} solve a small mystery with deduction.",
        f"Tell a child-friendly suspense story where a missing {p.husk} is found with a little magic at {world.place.name}.",
        f"Write a short story about {p.child}, {p.vampire}, and a {p.husk} that ends calmly after the mystery is solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.get("child")
    vampire = world.get("vampire")
    husk = world.get("husk")
    magic = world.get("magic")
    clue_spot = world.facts["clue_spot"]

    return [
        QAItem(
            question=f"Who was looking for the missing {husk.label}?",
            answer=f"{child.label} was looking for the missing {husk.label} at {world.place.name}.",
        ),
        QAItem(
            question=f"How did {vampire.label} figure out where the {husk.label} was?",
            answer=f"{vampire.label} used careful deduction, followed the clues, and guessed that it was {clue_spot}.",
        ),
        QAItem(
            question=f"What small kind of magic helped during the search?",
            answer=f"A little {magic.label} helped {vampire.label} lift the corner and check without making a mess.",
        ),
        QAItem(
            question=f"How did the story feel before the {husk.label} was found?",
            answer=f"It felt suspenseful and a little tense because the {husk.label} was missing, but it stayed gentle and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question="What is deduction?",
            answer="Deduction is when someone uses clues and careful thinking to figure something out.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next.",
        ),
        QAItem(
            question="What is a husk?",
            answer="A husk is the dry outer covering of something like corn or a seed.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is something special or mysterious that can do things regular life cannot.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(garden).
place(kitchen).
place(porch).

child_maybe(mina). child_maybe(tess). child_maybe(nora). child_maybe(piper). child_maybe(lena). child_maybe(ivy).
vampire_maybe(ves). vampire_maybe(otto). vampire_maybe(bram). vampire_maybe(silas). vampire_maybe(ren).

husk(corn_husk).
husk(leaf_husk).
husk(paper_husk).

magic(moon_thread).
magic(spark_dust).
magic(warm_charm).

mystery(Place, H) :- place(Place), husk(H).
solvable(Place, H) :- mystery(Place, H).
story(Place, C, V, H, M) :- solvable(Place, H), child_maybe(C), vampire_maybe(V), magic(M).
#show story/5.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CHILDREN:
        lines.append(asp.fact("child_maybe", c.lower()))
    for v in VAMPIRES:
        lines.append(asp.fact("vampire_maybe", v.lower()))
    for h, _ in HUSKS:
        lines.append(asp.fact("husk", h.replace(" ", "_")))
    for m, _ in MAGIC:
        lines.append(asp.fact("magic", m.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story/5."))
    atoms = sorted(set(asp.atoms(model, "story")))
    py = []
    for place in PLACES:
        for child in CHILDREN:
            for vamp in VAMPIRES:
                for husk, _ in HUSKS:
                    for magic, _ in MAGIC:
                        py.append((place, child.lower(), vamp.lower(), husk.replace(" ", "_"), magic.replace(" ", "_")))
    py = sorted(set(py))
    if atoms == py:
        print(f"OK: clingo gate matches Python registry product ({len(atoms)} combinations).")
        return 0
    print("MISMATCH between clingo and python.")
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, c, v, h) for p in PLACES for c in CHILDREN for v in VAMPIRES for h, _ in HUSKS]


def explain_rejection(_: str) -> str:
    return "No story: the requested options do not form a reasonable small mystery."


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: vampire, husk, deduction, suspense, conflict, magic, slice of life.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--vampire", choices=VAMPIRES)
    ap.add_argument("--husk", choices=[h for h, _ in HUSKS])
    ap.add_argument("--magic", choices=[m for m, _ in MAGIC])
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
    if args.place and args.child and args.vampire and args.husk:
        pass
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.child:
        combos = [c for c in combos if c[1] == args.child]
    if args.vampire:
        combos = [c for c in combos if c[2] == args.vampire]
    if args.husk:
        combos = [c for c in combos if c[3] == args.husk]
    if not combos:
        raise StoryError(explain_rejection("invalid"))
    place, child, vampire, husk = rng.choice(combos)
    magic = args.magic or rng.choice([m for m, _ in MAGIC])[0] if False else rng.choice([m for m, _ in MAGIC])
    return StoryParams(place=place, child=child, vampire=vampire, husk=husk, magic=magic)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = deduce_world(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind} {e.label} " + " ".join(bits))
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
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


CURATED = [
    StoryParams(place="garden", child="Mina", vampire="Ves", husk="corn husk", magic="moon thread"),
    StoryParams(place="kitchen", child="Tess", vampire="Otto", husk="paper husk", magic="spark dust"),
    StoryParams(place="porch", child="Nora", vampire="Bram", husk="leaf husk", magic="warm charm"),
]


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
        print(asp_program("#show story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story/5."))
        for atom in sorted(set(asp.atoms(model, "story"))):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
