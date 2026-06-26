#!/usr/bin/env python3
"""
A small mystery storyworld about a tamarind grove, a radiating clue, and a smith
who helps solve what is hidden.

The world is built around:
- Foreshadowing: small signs appear before the reveal.
- Mystery to Solve: a missing object or secret is uncovered through clues.

This script is self-contained and follows the storyworld contract.
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
# Model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "smith"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str = "the tamarind grove"
    weather: str = "warm"


@dataclass
class Clue:
    id: str
    label: str
    reveal: str
    hint: str


@dataclass
class Suspect:
    id: str
    label: str
    motive: str
    behavior: str


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SCENES = {
    "grove": Scene(place="the tamarind grove", weather="warm"),
    "market": Scene(place="the little market lane", weather="bright"),
    "courtyard": Scene(place="the stone courtyard", weather="still"),
}

CLUES = {
    "glow": Clue(
        id="glow",
        label="a faint glow",
        reveal="the clue glowed when the sun hit it",
        hint="It looked as if it wanted to be noticed.",
    ),
    "crumbs": Clue(
        id="crumbs",
        label="crumbs of tamarind shell",
        reveal="the crumbs pointed toward the storage shed",
        hint="Something had been opened there recently.",
    ),
    "ring": Clue(
        id="ring",
        label="a silver ring",
        reveal="the ring had smith marks inside",
        hint="It was made by a careful hand.",
    ),
    "thread": Clue(
        id="thread",
        label="a piece of red thread",
        reveal="the thread matched a bundle tied near the well",
        hint="It had been tied by someone in a hurry.",
    ),
}

SUSPECTS = {
    "market_child": Suspect(
        id="market_child",
        label="the market child",
        motive="wanted the sweet tamarind paste for a snack",
        behavior="kept looking at the jars and hiding sticky fingers",
    ),
    "gardener": Suspect(
        id="gardener",
        label="the gardener",
        motive="had moved the crates and knew the paths well",
        behavior="was calm but kept glancing at the shed",
    ),
    "smith": Suspect(
        id="smith",
        label="the smith",
        motive="had made the ring and noticed tiny marks others missed",
        behavior="was quiet, watchful, and careful with tools",
    ),
}

NAMES = ["Mina", "Taro", "Lila", "Noor", "Pia", "Beni"]
TRAITS = ["curious", "careful", "patient", "sharp-eyed", "gentle"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    scene: str
    clue: str
    suspect: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
clue_kind(C) :- clue(C).
suspect(S) :- suspect(S).
valid(Scene,Clue,Suspect) :- scene(Scene), clue(Clue), suspect(Suspect), matching(Scene,Clue,Suspect).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    lines.append(asp.fact("matching", "grove", "glow", "smith"))
    lines.append(asp.fact("matching", "grove", "crumbs", "market_child"))
    lines.append(asp.fact("matching", "market", "thread", "gardener"))
    lines.append(asp.fact("matching", "courtyard", "ring", "smith"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def choose_suspect(clue_id: str) -> str:
    if clue_id == "glow":
        return "smith"
    if clue_id == "crumbs":
        return "market_child"
    if clue_id == "ring":
        return "smith"
    if clue_id == "thread":
        return "gardener"
    raise StoryError("Unknown clue.")


def generate_world(params: StoryParams) -> World:
    scene = SCENES[params.scene]
    world = World(scene)

    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    smith = world.add(Entity(id="smith", kind="character", type="smith", label="the smith"))
    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]

    if params.suspect != choose_suspect(params.clue):
        raise StoryError("That clue does not reasonably lead to that suspect.")

    world.facts = {
        "hero": hero,
        "smith": smith,
        "clue": clue,
        "suspect": suspect,
        "scene": scene,
    }

    # Act 1: setup and foreshadowing.
    world.say(
        f"{hero.id} liked visiting {scene.place}, where the air smelled faintly of tamarind."
    )
    world.say(
        f"At the edge of the path stood {smith.label}, whose hammer made the morning seem to radiate with tiny bright sparks."
    )
    world.say(
        f"Before anything went wrong, {hero.id} noticed {clue.hint}"
    )

    # Act 2: mystery.
    world.para()
    world.say(
        f"Then a small thing went missing: the answer everyone needed to find."
    )
    world.say(
        f"People whispered that {suspect.label} might know more, because {suspect.behavior}."
    )
    world.say(
        f"{hero.id} looked again and saw {clue.label}; {clue.reveal}."
    )
    if params.clue in {"glow", "ring"}:
        world.say(
            f"That made {hero.id} think of {smith.label}, because the mark felt made by careful hands."
        )
    else:
        world.say(
            f"That made {hero.id} think of the nearby paths, where someone could slip away quietly."
        )

    # Act 3: resolution.
    world.para()
    if params.suspect == "smith":
        world.say(
            f"{smith.label} smiled and explained the missing thing had been set aside for safety, not stolen."
        )
        world.say(
            f"With the clue solved, {hero.id} found the hidden object near the workbench, right where the light had been pointing."
        )
    elif params.suspect == "market_child":
        world.say(
            f"The market child admitted to taking the sweet tamarind jar, but only to share it at snack time."
        )
        world.say(
            f"{hero.id} helped carry it back, and the mystery ended with sticky fingers and a laugh."
        )
    else:
        world.say(
            f"The gardener had moved the item to keep it safe from rain, and the missing thing was found beside the storage steps."
        )
        world.say(
            f"{hero.id} and {smith.label} put everything back in order, and the grove felt calm again."
        )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = f["clue"]
    suspect: Suspect = f["suspect"]
    return [
        f"Write a short mystery for a young child in a tamarind grove with {clue.label} as an important clue.",
        f"Tell a foreshadowing story where {f['hero'].id} notices something small before the mystery is solved.",
        f"Write a gentle mystery that leads to {suspect.label} and ends with the problem explained clearly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    clue: Clue = f["clue"]
    suspect: Suspect = f["suspect"]
    scene: Scene = f["scene"]
    return [
        QAItem(
            question=f"Where did {hero.id} look for clues?",
            answer=f"{hero.id} looked in {scene.place}, where the tamarind smell and the clue made the mystery feel close.",
        ),
        QAItem(
            question=f"What small sign foreshadowed the mystery?",
            answer=f"The foreshadowing sign was {clue.label}. It hinted that something important was waiting to be found.",
        ),
        QAItem(
            question=f"Who seemed connected to the mystery?",
            answer=f"{suspect.label} seemed connected because {suspect.behavior} and the clue pointed that way.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The mystery ended when the hidden thing was found and the reason for it was explained clearly.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a smith?",
            answer="A smith is a person who shapes metal with tools and heat.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives small hints early so readers can guess that something important may happen later.",
        ),
        QAItem(
            question="What is tamarind?",
            answer="Tamarind is a tangy fruit with brown pods and a sweet-sour taste.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story problem where something is hidden or not understood until clues help solve it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small tamarind mystery storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
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
    scene = args.scene or rng.choice(list(SCENES))
    clue = args.clue or rng.choice(list(CLUES))
    suspect = args.suspect or choose_suspect(clue)
    if args.suspect and args.clue and args.suspect != choose_suspect(args.clue):
        raise StoryError("That clue does not reasonably match the chosen suspect.")
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(scene=scene, clue=clue, suspect=suspect, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} location={e.location}")
    lines.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valids() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = {
        (scene, clue, suspect)
        for scene in SCENES
        for clue in CLUES
        for suspect in SUSPECTS
        if suspect == choose_suspect(clue)
    }
    model = asp.one_model(asp_program("#show valid/3."))
    cl = set(asp.atoms(model, "valid"))
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid combinations.")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(scene="grove", clue="glow", suspect="smith", name="Mina", trait="sharp-eyed"),
    StoryParams(scene="grove", clue="crumbs", suspect="market_child", name="Taro", trait="curious"),
    StoryParams(scene="courtyard", clue="ring", suspect="smith", name="Lila", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valids()
        for row in vals:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
