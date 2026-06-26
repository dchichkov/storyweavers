#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ugly_loin_symbolic_foreshadowing_flashback_moral_value.py
================================================================================================

A tiny detective-story world built from the seed words:
ugly, loin, symbolic.

The world centers on a small mystery with a clue that looks ugly at first,
a symbolic object tied to the suspect's past, and narrative instruments used
as real state: foreshadowing, flashback, and moral value.

The story is meant to feel like a child-friendly detective tale:
a clear beginning, a clue-driven middle, and a resolution that changes what
the characters understand about each other.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle", "detective"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    name: str
    indoors: bool = True
    smells: str = ""
    hides: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    symbolic: bool = False
    ugly: bool = False
    traces: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    suspect: str
    hero_name: str
    sidekick_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Location) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "alley": Location("the narrow alley", indoors=False, smells="wet stone", hides={"smudge", "footprint"}),
    "museum": Location("the little museum", indoors=True, smells="dust and old paper", hides={"display", "note"}),
    "attic": Location("the attic", indoors=True, smells="dry wood", hides={"trunk", "box"}),
}

CLUES = {
    "smudge": Clue(
        id="smudge",
        label="ugly smudge",
        phrase="an ugly dark smudge",
        kind="smudge",
        ugly=True,
        traces={"paint", "ash"},
    ),
    "loincloth": Clue(
        id="loincloth",
        label="symbolic loincloth",
        phrase="a symbolic loincloth with painted stripes",
        kind="cloth",
        symbolic=True,
        traces={"theater", "mask", "costume"},
    ),
    "ribbon": Clue(
        id="ribbon",
        label="symbolic ribbon",
        phrase="a symbolic ribbon tied in a careful knot",
        kind="ribbon",
        symbolic=True,
        traces={"gift", "memory", "promise"},
    ),
}

SUSPECTS = {
    "caretaker": "the caretaker",
    "actor": "the stage actor",
    "uncle": "the uncle",
}

# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
class Scene:
    def __init__(self, world: World, detective: Entity, sidekick: Entity, suspect: Entity, clue: Clue) -> None:
        self.world = world
        self.detective = detective
        self.sidekick = sidekick
        self.suspect = suspect
        self.clue = clue
        self.evidence: list[str] = []


def introduce(world: World, detective: Entity, sidekick: Entity, clue: Clue) -> None:
    world.say(
        f"{detective.id} was a careful little detective who liked noticing tiny things."
    )
    world.say(
        f"{sidekick.id} kept a notebook and said the {clue.label} looked strange, but worth a closer look."
    )


def foreshadow(world: World, clue: Clue) -> None:
    if clue.symbolic:
        world.say(
            f"The {clue.label} seemed ugly at first, yet its shape felt symbolic, like it was trying to say something."
        )
    else:
        world.say(
            f"The clue looked ugly at first, but it had a pattern that made the detective pause."
        )
    world.facts["foreshadowed"] = True


def flashback(world: World, suspect: Entity, clue: Clue) -> None:
    if clue.id == "loincloth":
        world.say(
            f"Then the detective remembered a flashback: the {suspect.label} had once worn the same cloth in a neighborhood play."
        )
        world.say(
            f"In that memory, the cloth was not a secret tool at all; it was a costume piece with a proud job."
        )
    elif clue.id == "ribbon":
        world.say(
            f"Then came a flashback: the ribbon had been tied around a gift box long ago, when the family made a promise."
        )
    else:
        world.say(
            f"Then came a flashback: the dark mark matched old paint from a long-ago cleanup."
        )
    world.facts["flashback"] = True


def suspect_behavior(world: World, suspect: Entity, clue: Clue) -> None:
    if clue.symbolic:
        suspect.memes["nervous"] = suspect.memes.get("nervous", 0) + 1
        world.say(
            f"{suspect.id} looked nervous, because the thing was tied to a memory, not just to the day of the mystery."
        )
    else:
        world.say(f"{suspect.id} kept very still, as if waiting to see what the detective would notice next.")


def investigation(world: World, scene: Scene) -> None:
    clue = scene.clue
    scene.evidence.append(clue.kind)
    world.say(
        f"{scene.detective.id} knelt near the clue and checked the floor, the walls, and the old shelf beside it."
    )
    if clue.traces:
        world.say(
            f"The marks nearby matched {', '.join(sorted(clue.traces))}, which helped narrow the mystery."
        )
    if clue.ugly:
        world.say(
            f"The clue was ugly, but ugly things can still be useful when a detective studies them carefully."
        )
    world.facts["evidence"] = list(scene.evidence)


def solve(world: World, scene: Scene) -> None:
    clue = scene.clue
    suspect = scene.suspect
    if clue.id == "loincloth":
        world.say(
            f"At last, {scene.detective.id} smiled. The symbolic loincloth belonged to the {suspect.label}, and it had fallen from a costume trunk."
        )
        world.say(
            f"It was not proof of trouble at all; it was proof that the {suspect.label} had been rehearsing for a small show."
        )
    elif clue.id == "ribbon":
        world.say(
            f"At last, {scene.detective.id} smiled. The symbolic ribbon belonged to the family, and the mystery was really about a forgotten promise."
        )
    else:
        world.say(
            f"At last, {scene.detective.id} smiled. The ugly smudge came from old paint on a moving crate, not from a crime."
        )
    world.facts["solved"] = True


def moral_value(world: World, clue: Clue, suspect: Entity) -> None:
    if clue.symbolic:
        world.say(
            f"The detective learned a moral value: people may hide a symbol because it matters to them, not because they mean harm."
        )
    else:
        world.say(
            f"The detective learned a moral value: a messy mark is easier to judge than to understand, so it is wise to look twice."
        )
    world.say(
        f"{suspect.id} thanked the detective, and the strange object finally made sense."
    )
    world.facts["moral_value"] = True


def tell(place: Location, clue: Clue, suspect_name: str, hero_name: str, sidekick_name: str) -> World:
    world = World(place)
    detective = world.add(Entity(id=hero_name, kind="character", type="detective", label=hero_name))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="girl", label=sidekick_name))
    suspect = world.add(Entity(id=suspect_name, kind="character", type="man", label=suspect_name))
    clue_ent = world.add(Entity(
        id=clue.id,
        kind="thing",
        type=clue.kind,
        label=clue.label,
        phrase=clue.phrase,
        owner=suspect.id,
        plural=False,
        meters={"notice": 1.0},
        memes={"meaning": 1.0 if clue.symbolic else 0.0},
    ))

    world.facts.update(
        place=place,
        clue=clue,
        suspect=suspect,
        detective=detective,
        sidekick=sidekick,
        clue_ent=clue_ent,
    )

    world.say(f"{detective.id} came to {place.name}, where the air smelled like {place.smells}.")
    world.say(f"On the floor, there was {clue.phrase}.")
    introduce(world, detective, sidekick, clue)
    world.para()
    foreshadow(world, clue)
    suspect_behavior(world, suspect, clue)
    investigation(world, Scene(world, detective, sidekick, suspect, clue))
    world.para()
    flashback(world, suspect, clue)
    solve(world, Scene(world, detective, sidekick, suspect, clue))
    moral_value(world, clue, suspect)
    return world


# ---------------------------------------------------------------------------
# Question/answer material
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = f["clue"]
    place: Location = f["place"]
    suspect: Entity = f["suspect"]
    return [
        f'Write a short detective story for children set in {place.name} about {clue.label} and a patient clue search.',
        f"Tell a small mystery where {f['detective'].id} follows {clue.phrase} and learns what it really means.",
        f"Write a gentle detective tale that uses the words ugly, loin, and symbolic, and ends with a moral value.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: Clue = f["clue"]
    suspect: Entity = f["suspect"]
    detective: Entity = f["detective"]
    place: Location = f["place"]
    qa = [
        QAItem(
            question=f"Where did {detective.id} look for clues?",
            answer=f"{detective.id} looked in {place.name}, where the air smelled like {place.smells}.",
        ),
        QAItem(
            question=f"Why did the {clue.label} matter?",
            answer=(
                f"It mattered because it was more than a messy thing. "
                f"It gave {detective.id} a real clue about the mystery."
            ),
        ),
        QAItem(
            question=f"What did the detective learn about the {suspect.label}?",
            answer=(
                f"{detective.id} learned the {suspect.label} was not causing harm. "
                f"The clue fit a memory or a costume, so the strange object had a harmless meaning."
            ),
        ),
    ]
    if f.get("solved"):
        qa.append(
            QAItem(
                question="How was the mystery solved?",
                answer=(
                    f"{detective.id} checked the clue, remembered the flashback, and noticed the symbolic meaning. "
                    f"That turned the ugly-looking object into an understandable part of the story."
                ),
            )
        )
    return qa


WORLD_QA = [
    QAItem(
        question="What is foreshadowing in a story?",
        answer=(
            "Foreshadowing is a hint that helps you guess something important before it happens."
        ),
    ),
    QAItem(
        question="What is a flashback?",
        answer=(
            "A flashback is a part of a story that remembers something from before the current scene."
        ),
    ),
    QAItem(
        question="What is a moral value in a story?",
        answer=(
            "A moral value is the lesson or wise idea the story leaves you with."
        ),
    ),
    QAItem(
        question="What does symbolic mean?",
        answer=(
            "Symbolic means something stands for a bigger idea, memory, or feeling."
        ),
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for q in WORLD_QA:
        out.append(q)
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_place(P) :- place(P).
clue_kind(C) :- clue(C).

symbolic_clue(C) :- clue_symbolic(C).
ugly_clue(C) :- clue_ugly(C).

hint(C) :- symbolic_clue(C).
hint(C) :- ugly_clue(C).

flashback_needed(C) :- symbolic_clue(C).
moral_needed(C) :- clue(C).

solved(C) :- hint(C), flashback_needed(C), moral_needed(C).

#show solved/1.
#show hint/1.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for h in sorted(place.hides):
            lines.append(asp.fact("hides", pid, h))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.symbolic:
            lines.append(asp.fact("clue_symbolic", cid))
        if clue.ugly:
            lines.append(asp.fact("clue_ugly", cid))
        for t in sorted(clue.traces):
            lines.append(asp.fact("trace", cid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solve() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    return sorted(set(asp.atoms(model, "solved")))


def asp_verify() -> int:
    asp_set = set(asp_solve())
    py_set = set((cid,) for cid, clue in CLUES.items() if clue.symbolic or clue.ugly)
    if asp_set == py_set:
        print(f"OK: ASP parity matches Python gate ({len(asp_set)} clues).")
        return 0
    print("MISMATCH between ASP and Python:")
    if asp_set - py_set:
        print("  only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Validation and generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for clue in CLUES:
            for suspect in SUSPECTS:
                if clue == "loincloth" and place == "museum":
                    combos.append((place, clue, suspect))
                elif clue == "smudge" and place in {"alley", "attic"}:
                    combos.append((place, clue, suspect))
                elif clue == "ribbon" and place == "attic":
                    combos.append((place, clue, suspect))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if args.suspect:
        combos = [c for c in combos if c[2] == args.suspect]
    if not combos:
        raise StoryError("(No valid detective story matches the given options.)")
    place, clue, suspect = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(["Milo", "Nina", "Tess", "Arlo", "June"])
    sidekick = args.sidekick or rng.choice(["Bea", "Pip", "Lena", "Owen", "Mina"])
    return StoryParams(place=place, clue=clue, suspect=suspect, hero_name=hero_name, sidekick_name=sidekick)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CLUES[params.clue], SUSPECTS[params.suspect], params.hero_name, params.sidekick_name)
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_solve())} ASP-solvable clue patterns:")
        for (cid,) in asp_solve():
            print(f"  {cid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="museum", clue="loincloth", suspect="actor", hero_name="Milo", sidekick_name="Bea"),
            StoryParams(place="alley", clue="smudge", suspect="caretaker", hero_name="Nina", sidekick_name="Pip"),
            StoryParams(place="attic", clue="ribbon", suspect="uncle", hero_name="Tess", sidekick_name="Lena"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero_name}: {p.clue} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
