#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cannibal_blood_spectacle_foreshadowing_curiosity_detective_story.py
===============================================================================================

A small detective-style story world built from the seed words:
cannibal, blood, spectacle.

The story stays child-facing by treating "cannibal" as the title of a spooky
stage act, "blood" as red stage paint, and "spectacle" as a theater event.
The narrative features foreshadowing and curiosity, with a clear mystery, clues,
a turn, and a resolution.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    kind: str
    has_stage: bool = False
    has_backstage: bool = False
    has_red_paint: bool = False
    has_fog_machine: bool = False


@dataclass
class StoryParams:
    place: str
    detective_name: str
    helper_name: str
    suspect_name: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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

PLACES = {
    "the theater": Place(name="the theater", kind="theater", has_stage=True, has_backstage=True, has_red_paint=True, has_fog_machine=True),
    "the carnival tent": Place(name="the carnival tent", kind="carnival", has_stage=True, has_backstage=True, has_red_paint=True, has_fog_machine=True),
    "the school hall": Place(name="the school hall", kind="hall", has_stage=True, has_backstage=True, has_red_paint=True, has_fog_machine=False),
}

DETECTIVE_NAMES = ["Mira", "Nico", "Luna", "Theo", "Ivy", "Bram"]
HELPER_NAMES = ["Pip", "June", "Otis", "Mina", "Bea", "Jules"]
SUSPECT_NAMES = ["Mr. Reed", "Ms. Bell", "Coach Finn", "Aunt Wren", "Mr. Moss"]

# Inline ASP rules; the story's gate is: curiosity finds clues, foreshadowing
# predicts the truth, and the red "blood" is only stage paint.
ASP_RULES = r"""
#show clue/2.
#show foreshadow/2.
#show resolve/2.

clue(D, paint) :- detective(D), red_paint(scene).
clue(D, fog) :- detective(D), fog_machine(scene).
foreshadow(D, paint) :- clue(D, paint).
foreshadow(D, fog) :- clue(D, fog).
resolve(D, paint_spill) :- foreshadow(D, paint), foreshadow(D, fog).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.kind))
        if p.has_stage:
            lines.append(asp.fact("stage", p.kind))
        if p.has_backstage:
            lines.append(asp.fact("backstage", p.kind))
        if p.has_red_paint:
            lines.append(asp.fact("red_paint", "scene"))
        if p.has_fog_machine:
            lines.append(asp.fact("fog_machine", "scene"))
    lines.append(asp.fact("detective", "detective"))
    return "\n".join(lines)


def asp_program(show: str = "#show resolve/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place=place)
    det = world.add(Entity(id="detective", kind="character", label=params.detective_name, type="girl"))
    helper = world.add(Entity(id="helper", kind="character", label=params.helper_name, type="boy"))
    suspect = world.add(Entity(id="suspect", kind="character", label=params.suspect_name, type="woman"))

    world.facts.update(detective=det, helper=helper, suspect=suspect, place=place)

    # Simulated state: curiosity rises, clues appear, foreshadowing accumulates.
    det.memes["curiosity"] = 2.0
    helper.memes["worry"] = 1.0
    suspect.memes["nervous"] = 1.0

    return world


def tell_story(world: World) -> None:
    det = world.facts["detective"]
    helper = world.facts["helper"]
    suspect = world.facts["suspect"]
    place = world.place

    world.say(
        f"{det.label} was a small detective who loved a good puzzle, and {helper.label} liked to carry a notebook."
    )
    world.say(
        f"One evening at {place.name}, there was a strange spectacle called The Cannibal Shadow Show."
    )
    world.say(
        f"Before the curtain even rose, {det.label} noticed a tiny red smear near the steps, like blood."
    )

    world.para()
    world.say(
        f"{det.label}'s curiosity grew. {det.pronoun().capitalize()} looked for more clues, because the red mark did not belong on the stage."
    )
    if place.has_fog_machine:
        world.say(
            f"Then {det.label} saw the fog machine puffing next to a tipped paint cup, and that made a quiet foreshadowing in {det.pronoun('possessive')} mind."
        )
    else:
        world.say(
            f"Then {det.label} found a tipped paint cup behind a prop box, and that gave the mystery a clearer shape."
        )
    world.say(
        f"{suspect.label} stood nearby with a startled face, holding a brush for the spooky set."
    )

    world.para()
    world.say(
        f"{det.label} asked gentle questions instead of accusing anyone. {det.pronoun().capitalize()} learned that the 'blood' was only red stage paint for the cannibal costume."
    )
    world.say(
        f"The paint had spilled when the prop cart bumped the step, so the scary-looking clue was actually a simple accident."
    )
    world.say(
        f"{helper.label} smiled and wrote it down, and {suspect.label} sighed with relief."
    )

    world.para()
    world.say(
        f"At the end, the curtain opened on the spectacle, the stage was cleaned, and {det.label} felt proud of {det.pronoun('possessive')} curiosity."
    )
    world.say(
        f"The mystery had looked spooky at first, but the real answer was small, clear, and harmless."
    )

    world.facts["resolved"] = True
    world.facts["blood"] = "stage paint"
    world.facts["spectacle"] = "The Cannibal Shadow Show"
    world.facts["foreshadowing"] = True
    world.facts["curiosity"] = True


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.place.name
    return [
        f"Write a detective story for a young child set at {p} with foreshadowing and curiosity.",
        "Tell a mystery where a small detective finds a clue that looks like blood but turns out to be stage paint.",
        "Write a short, gentle story about a spooky spectacle called The Cannibal Shadow Show and solve the mystery kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    det = world.facts["detective"]
    helper = world.facts["helper"]
    suspect = world.facts["suspect"]
    place = world.place.name
    return [
        QAItem(
            question=f"Where did {det.label} solve the mystery?",
            answer=f"{det.label} solved the mystery at {place}, where the spooky spectacle was happening.",
        ),
        QAItem(
            question="What did the red blood-like clue really turn out to be?",
            answer="It turned out to be red stage paint, not real blood.",
        ),
        QAItem(
            question=f"How did {det.label} act while solving the case?",
            answer=f"{det.label} stayed curious, asked gentle questions, and followed the clues instead of making a big fuss.",
        ),
        QAItem(
            question=f"Who helped {det.label} keep track of the clues?",
            answer=f"{helper.label} helped by carrying a notebook and writing things down.",
        ),
        QAItem(
            question=f"Why was {suspect.label} relieved at the end?",
            answer=f"{suspect.label} was relieved because the spooky-looking mess was only spilled paint from the costume show.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when small clues hint at what will happen later in a story.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look, ask, and learn more about what is happening.",
        ),
        QAItem(
            question="Why can stage blood be safe in a show?",
            answer="Stage blood can be safe because it is pretend blood made for costumes and theater scenes.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------

def asp_validations() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show resolve/2."))
    return sorted(set(asp.atoms(model, "resolve")))


def python_validations() -> list[tuple[str, str]]:
    return [("detective", "paint_spill")]


def asp_verify() -> int:
    a = set(asp_validations())
    p = set(python_validations())
    if a == p:
        print("OK: ASP and Python validation match.")
        return 0
    print("MISMATCH:")
    print("ASP:", sorted(a))
    print("PY :", sorted(p))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective story world with foreshadowing and curiosity.")
    ap.add_argument("--place", choices=sorted(PLACES.keys()))
    ap.add_argument("--detective-name", choices=DETECTIVE_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--suspect-name", choices=SUSPECT_NAMES)
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
    place = args.place or rng.choice(sorted(PLACES.keys()))
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    suspect_name = args.suspect_name or rng.choice(SUSPECT_NAMES)
    if detective_name == helper_name:
        raise StoryError("detective and helper must have different names")
    return StoryParams(
        place=place,
        detective_name=detective_name,
        helper_name=helper_name,
        suspect_name=suspect_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place={world.place.name}")
    for ent in world.entities.values():
        bits = []
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        lines.append(f"{ent.id}: {ent.label} ({ent.type}) {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
    StoryParams(place="the theater", detective_name="Mira", helper_name="Pip", suspect_name="Ms. Bell"),
    StoryParams(place="the carnival tent", detective_name="Nico", helper_name="June", suspect_name="Mr. Reed"),
    StoryParams(place="the school hall", detective_name="Ivy", helper_name="Otis", suspect_name="Aunt Wren"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolve/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolve/2."))
        print(f"resolve atoms: {sorted(set(asp.atoms(model, 'resolve')))}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
