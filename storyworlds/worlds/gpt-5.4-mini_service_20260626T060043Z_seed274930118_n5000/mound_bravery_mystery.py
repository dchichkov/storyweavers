#!/usr/bin/env python3
"""
storyworlds/worlds/mound_bravery_mystery.py
===========================================

A small mystery storyworld about a child, a mound, and a brave choice.

Premise:
A child notices a strange mound in a quiet place and wants to know what is
hidden there. The child is uneasy, because the mound could hide something scary
or important.

Turn:
The child listens, looks closely, asks for help, and gathers a clue. Bravery
means acting while still feeling a little afraid.

Resolution:
The mound's mystery is solved in a gentle way, and the child learns that being
brave does not mean feeling no fear. It means moving carefully anyway.
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
    uncovered: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    quiet: bool = True
    kinds: set[str] = field(default_factory=set)


@dataclass
class Mound:
    id: str
    label: str
    shape: str
    surface: str
    clue: str
    reveals: str
    hides_kind: str
    fear_kind: str = "dark"
    brave_kind: str = "bravery"


@dataclass
class StoryParams:
    place: str
    mound: str
    child_name: str
    child_gender: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


def _subject_name(e: Entity) -> str:
    return e.id


def _poss(e: Entity) -> str:
    return e.pronoun("possessive")


def _child_desc(child: Entity) -> str:
    trait = next((t for t in child.traits if t != "little"), "curious")
    return f"little {trait} {child.type}"


def _mound_story_label(mound: Mound) -> str:
    return mound.label


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mound = MOUNDS[params.mound]
    world = World(place)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        traits=["little", params.trait],
        meters={"steps": 0.0},
        memes={"curiosity": 0.0, "fear": 0.0, "bravery": 0.0, "relief": 0.0},
    ))
    mound_ent = world.add(Entity(
        id="mound",
        kind="thing",
        type="mound",
        label=mound.label,
        phrase=mound.shape,
        meters={"stillness": 1.0, "size": 1.0},
        memes={"mystery": 1.0},
    ))
    hidden = world.add(Entity(
        id="hidden",
        kind="thing",
        type=mound.hides_kind,
        label=mound.reveals,
        phrase=mound.reveals,
        uncovered=False,
        meters={"safety": 1.0},
        memes={"lost": 1.0},
    ))
    world.facts.update(child=child, mound=mound, mound_ent=mound_ent, hidden=hidden)
    return world


def tell_story(world: World) -> None:
    child: Entity = world.facts["child"]
    mound: Mound = world.facts["mound"]
    mound_ent: Entity = world.facts["mound_ent"]
    hidden: Entity = world.facts["hidden"]

    world.say(
        f"{_subject_name(child)} was a {_child_desc(child)} who liked quiet places."
    )
    world.say(
        f"One day, {child.id} found {_mound_story_label(mound)} at {world.place.label}."
    )
    world.say(
        f"The mound was {mound.shape}, and it looked strange because the top was "
        f"{mound.surface}."
    )
    child.memes["curiosity"] += 1
    child.memes["fear"] += 1
    world.say(
        f"{child.id} felt curious, but { _poss(child) } heart gave a tiny bump of worry."
    )

    world.para()
    world.say(
        f"{child.id} listened first. The mound stayed still, but a soft sound came from inside."
    )
    world.say(
        f"That sound made the mystery feel bigger, so {child.id} took one brave step closer."
    )
    child.meters["steps"] += 1
    child.memes["bravery"] += 1

    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f"{child.id} was still scared, yet {child.pronoun().capitalize()} did not run away."
        )
    world.say(
        f"{child.id} used a small stick to nudge the loose dirt at the edge of the mound."
    )
    mound_ent.meters["opened"] = 1.0

    world.para()
    world.say(
        f"Under the dirt, {child.id} found {hidden.label}, just as the mound had promised."
    )
    hidden.uncovered = True
    hidden.memes["lost"] = 0.0
    child.memes["relief"] += 1
    child.memes["fear"] = 0.0
    world.say(
        f"It was not a monster at all. It was {mound.reveals}, and it had been hidden by the mound."
    )
    world.say(
        f"{child.id} felt brave at once, because {child.pronoun().capitalize()} had looked carefully and found the truth."
    )
    world.say(
        f"In the end, the mound was not scary anymore; it was only a small place that kept a secret until someone brave asked gently."
    )

    world.facts["solved"] = True


def aspiration_text(world: World) -> str:
    child: Entity = world.facts["child"]
    mound: Mound = world.facts["mound"]
    return (
        f"Write a short mystery story for a young child about {child.id}, "
        f"a brave choice, and a strange mound at {world.place.label}."
        f" Include a gentle clue and a clear ending."
    )


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    mound: Mound = world.facts["mound"]
    return [
        aspiration_text(world),
        f"Tell a child-friendly mystery where {child.id} feels nervous about {_mound_story_label(mound)} but acts bravely.",
        f"Write a short story about a mound, a secret, and someone who is brave enough to look closer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    mound: Mound = world.facts["mound"]
    hidden: Entity = world.facts["hidden"]
    return [
        QAItem(
            question=f"What did {child.id} find at {world.place.label}?",
            answer=f"{child.id} found {_mound_story_label(mound)} at {world.place.label}. It looked strange and kept a secret inside.",
        ),
        QAItem(
            question=f"Why did {child.id} feel worried about the mound?",
            answer=(
                f"{child.id} felt worried because the mound was quiet, looked unusual, and might have hidden something unknown."
            ),
        ),
        QAItem(
            question=f"What was the mystery hidden under the mound?",
            answer=f"Under the mound was {hidden.label}. It was not dangerous; it was only something that had been hidden away.",
        ),
        QAItem(
            question=f"How did {child.id} show bravery?",
            answer=(
                f"{child.id} showed bravery by staying close, listening first, and nudging the dirt carefully instead of running away."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    mound: Mound = world.facts["mound"]
    return [
        QAItem(
            question="What is a mound?",
            answer="A mound is a small hill or pile of earth that rises up from the ground.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something careful and helpful even when you feel a little scared.",
        ),
        QAItem(
            question="Why do mysteries make people look closely?",
            answer="Mysteries make people look closely because they want to find out what is true instead of guessing.",
        ),
        QAItem(
            question=f"What kind of hidden thing was in this story's mound?",
            answer=f"It was a {mound.hides_kind}. The story uses a gentle hidden thing so the mystery can feel safe and child-friendly.",
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.uncovered:
            parts.append("uncovered=True")
        lines.append(f"{e.id}: {e.type} " + " ".join(parts))
    lines.append(f"place={world.place.label}")
    return "\n".join(lines)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.mound not in MOUNDS:
        raise StoryError("Unknown mound type.")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError("Child gender must be girl or boy.")


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.quiet:
            lines.append(asp.fact("quiet", pid))
        for k in sorted(place.kinds):
            lines.append(asp.fact("has_kind", pid, k))
    for mid, mound in MOUNDS.items():
        lines.append(asp.fact("mound", mid))
        lines.append(asp.fact("hides_kind", mid, mound.hides_kind))
        lines.append(asp.fact("reveals", mid, mound.reveals))
        lines.append(asp.fact("fear_kind", mid, mound.fear_kind))
        lines.append(asp.fact("brave_kind", mid, mound.brave_kind))
    return "\n".join(lines)


ASP_RULES = r"""
possible_mystery(P, M) :- place(P), mound(M), quiet(P), has_kind(P, mound), reveals(M, _).
brave_story(P, M) :- possible_mystery(P, M), fear_kind(M, fear), brave_kind(M, bravery).
#show brave_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show brave_story/2."))
    asp_set = set(asp.atoms(model, "brave_story"))
    py_set = {(p, m) for p, place in PLACES.items() for m, mound in MOUNDS.items() if place.quiet and "mound" in place.kinds}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(asp_set)} combinations).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if asp_set - py_set:
        print("  only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in Python:", sorted(py_set - asp_set))
    return 1


PLACES = {
    "field": Place(id="field", label="the field", quiet=True, kinds={"mound"}),
    "garden": Place(id="garden", label="the garden", quiet=True, kinds={"mound"}),
    "yard": Place(id="yard", label="the yard", quiet=True, kinds={"mound"}),
}

MOUNDS = {
    "grass_mound": Mound(
        id="grass_mound",
        label="a little grass-covered mound",
        shape="soft and round",
        surface="damp with dew",
        clue="a soft sound",
        reveals="a lost kitten",
        hides_kind="kitten",
    ),
    "leaf_mound": Mound(
        id="leaf_mound",
        label="a mound of leaves",
        shape="tiny and lumpy",
        surface="rustling at the top",
        clue="a fluttering sound",
        reveals="a shiny marble",
        hides_kind="marble",
    ),
    "soil_mound": Mound(
        id="soil_mound",
        label="a neat soil mound",
        shape="small and tidy",
        surface="crumbly at the edge",
        clue="a quiet scratching",
        reveals="a buried key",
        hides_kind="key",
    ),
}

TRAITS = ["curious", "careful", "gentle", "bold", "quiet", "thoughtful"]
NAMES = ["Mia", "Leo", "Nora", "Ben", "Lily", "Eli", "Ava", "Finn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly mystery about a mound and a brave choice.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--mound", choices=sorted(MOUNDS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(PLACES))
    mound = args.mound or rng.choice(list(MOUNDS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mound=mound, child_name=name, child_gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="field", mound="grass_mound", child_name="Mia", child_gender="girl", trait="curious"),
    StoryParams(place="garden", mound="leaf_mound", child_name="Leo", child_gender="boy", trait="careful"),
    StoryParams(place="yard", mound="soil_mound", child_name="Nora", child_gender="girl", trait="bold"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show brave_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show brave_story/2."))
        print(f"{len(asp.atoms(model, 'brave_story'))} brave-story combinations")
        for p, m in sorted(set(asp.atoms(model, "brave_story"))):
            print(f"  {p} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.child_name}: {p.mound} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
