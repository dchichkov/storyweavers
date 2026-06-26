#!/usr/bin/env python3
"""
A small whodunit storyworld about a missing patch, a tray of silica, and a
few careful questions that lead to the truth.

The world is built from a tiny mystery premise:
- A child notices something odd.
- Dialogue reveals clues and misdirection.
- A surprise changes what the characters thought happened.
- Problem solving restores the missing object and ends the mystery.

This script is standalone and follows the Storyweavers world contract.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
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
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "detective"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old shed"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    label: str
    phrase: str
    kind: str
    location: str
    reveals: str


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    location: str
    hidden: bool = False
    owner: Optional[str] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "shed": Setting(place="the old shed", indoors=True, affords={"search"}),
    "attic": Setting(place="the attic", indoors=True, affords={"search"}),
    "library": Setting(place="the library corner", indoors=True, affords={"search"}),
    "garden": Setting(place="the garden path", indoors=False, affords={"search"}),
}

CHARACTERS = {
    "child": ("boy", "girl"),
    "detective": ("detective",),
    "neighbor": ("woman", "man"),
}

PROPS = {
    "patch": Prop(
        id="patch",
        label="patch",
        phrase="a faded red patch",
        location="under the chair",
        hidden=True,
    ),
    "silica": Prop(
        id="silica",
        label="silica",
        phrase="a small paper packet of silica",
        location="on the shelf",
        hidden=False,
    ),
    "lamp": Prop(
        id="lamp",
        label="lamp",
        phrase="a tiny brass lamp",
        location="by the window",
        hidden=False,
    ),
}

CLUES = {
    "silica": Clue(
        label="silica",
        phrase="a small paper packet of silica",
        kind="drying",
        location="on the shelf",
        reveals="the packet had soaked up dampness from the patch box",
    ),
    "patch": Clue(
        label="patch",
        phrase="a faded red patch",
        kind="fabric",
        location="under the chair",
        reveals="someone had tucked the patch there to hide it",
    ),
    "footprint": Clue(
        label="footprint",
        phrase="a little muddy footprint",
        kind="mud",
        location="near the door",
        reveals="the missing patch had been carried through the room",
    ),
}

NAMES = ["Mina", "Eli", "Nora", "Toby", "Iris", "Theo", "Lena", "Owen"]
TRAITS = ["curious", "careful", "quiet", "brave", "patient", "bright"]

ASP_RULES = r"""
% A simple whodunit compatibility model:
% a story is valid when the hidden patch can be found, silica is present as a clue,
% and the setting supports a search.

can_search(S) :- affords(S, search).

clue_present(silica) :- clue(silica).
clue_present(patch) :- hidden(patch).

mystery_valid(S) :- can_search(S), clue_present(silica), clue_present(patch).
"""


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if prop.hidden:
            lines.append(asp.fact("hidden", pid))
        lines.append(asp.fact("located", pid, prop.location))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery_valid/1."))
    return sorted(set(asp.atoms(model, "mystery_valid")))


def asp_verify() -> int:
    py = set((sid,) for sid, s in SETTINGS.items() if s.affords and "search" in s.affords)
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} settings).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    trait: str
    detective_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="shed", hero_name="Mina", hero_type="girl", trait="curious", detective_name="Detective Rae"),
    StoryParams(setting="attic", hero_name="Eli", hero_type="boy", trait="careful", detective_name="Detective Jun"),
    StoryParams(setting="library", hero_name="Nora", hero_type="girl", trait="patient", detective_name="Detective Wren"),
    StoryParams(setting="garden", hero_name="Theo", hero_type="boy", trait="quiet", detective_name="Detective Sol"),
]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    detective = world.add(Entity(id="detective", kind="character", type="detective", label=params.detective_name))
    neighbor = world.add(Entity(id="neighbor", kind="character", type="woman", label="Mrs. Bell"))

    patch = world.add(Entity(
        id="patch",
        kind="thing",
        type="patch",
        label="patch",
        phrase=PROPS["patch"].phrase,
        owner=neighbor.id,
        location="under the chair",
    ))
    silica = world.add(Entity(
        id="silica",
        kind="thing",
        type="silica",
        label="silica",
        phrase=PROPS["silica"].phrase,
        location="on the shelf",
    ))
    lamp = world.add(Entity(
        id="lamp",
        kind="thing",
        type="lamp",
        label="lamp",
        phrase=PROPS["lamp"].phrase,
        location="by the window",
    ))

    world.facts.update(
        hero=hero,
        detective=detective,
        neighbor=neighbor,
        patch=patch,
        silica=silica,
        lamp=lamp,
        trait=params.trait,
        setting=params.setting,
    )

    # Act 1: setup
    world.say(
        f"{params.hero_name} was a {params.trait} little {params.hero_type} who loved asking questions."
    )
    world.say(
        f"One afternoon, {params.hero_name} and {params.detective_name} met at {setting.place} to look for a missing patch."
    )
    world.say(
        f"{params.hero_name} noticed a small paper packet of silica on the shelf and wondered why it was there."
    )

    # Act 2: dialogue and surprise
    world.para()
    world.say(f'"Did you move the patch?" {params.hero_name} asked Mrs. Bell.')
    world.say(f'"No," she said. "I only opened the box and saw the silica. I thought it was just for keeping things dry."')
    world.say(f'"Less talk, more looking," said {params.detective_name}, and they searched the room carefully.')

    # Surprise: silica points to hidden dampness and the patch is not lost, just tucked away.
    world.say(
        f"Then {params.hero_name} found a little muddy footprint near the door, and the mystery changed at once."
    )
    world.say(
        f"The footprint meant someone had carried the patch across the room and hidden it under the chair."
    )

    # Act 3: problem solving
    world.para()
    world.say(
        f'{params.detective_name} crouched down and said, "If the silica was on the shelf, it must have been near the box when the room got damp."'
    )
    world.say(
        f'{params.hero_name} pulled back the chair, and there it was: {patch.phrase}, tucked safely away.'
    )
    world.say(
        f'Mrs. Bell laughed softly. "I put it there so I would not forget to patch the tear later," she said.'
    )
    world.say(
        f"{params.hero_name} handed the patch back, and the three of them smiled because the clue had solved the case."
    )

    world.facts.update(resolved=True, surprise=True)
    return world


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    detective = f["detective"]
    return [
        f'Write a short whodunit story for a child named {hero.label} that includes a patch and silica.',
        f"Tell a gentle mystery where {detective.label} and {hero.label} search {world.setting.place} and solve a small problem.",
        f'Write a simple dialogue-driven story with a surprise ending that uses the words "less", "patch", and "silica".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    detective = f["detective"]
    neighbor = f["neighbor"]
    return [
        QAItem(
            question=f"Who helped {hero.label} search for the missing patch?",
            answer=f"{detective.label} helped {hero.label} search for the missing patch.",
        ),
        QAItem(
            question=f"What clue did {hero.label} notice on the shelf?",
            answer="A small paper packet of silica was on the shelf.",
        ),
        QAItem(
            question=f"Where was the patch hiding at the end?",
            answer="The patch was hidden under the chair.",
        ),
        QAItem(
            question=f"Who said they had not moved the patch?",
            answer=f"{neighbor.label} said she had not moved the patch.",
        ),
        QAItem(
            question="What surprised everyone about the footprint?",
            answer="The muddy footprint showed that the patch had been carried and hidden, so the search should look near the door and the chair.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is silica used for?",
            answer="Silica can help keep things dry because it soaks up moisture.",
        ),
        QAItem(
            question="What is a patch?",
            answer="A patch is a piece of cloth used to cover or mend a hole or tear.",
        ),
        QAItem(
            question="Why do detectives ask questions?",
            answer="Detectives ask questions so they can find clues and figure out what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = [f"type={e.type}"]
        if e.label:
            parts.append(f"label={e.label}")
        if e.location:
            parts.append(f"location={e.location}")
        if e.hidden:
            parts.append("hidden=True")
        lines.append(f"  {e.id}: {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with dialogue, surprise, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--trait", choices=["curious", "careful", "quiet", "brave", "patient", "bright"])
    ap.add_argument("--detective-name")
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
    if args.gender and args.name is None:
        pass
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    hero_type = args.gender or rng.choice(["boy", "girl"])
    hero_name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    detective_name = args.detective_name or f"Detective {rng.choice(['Rae', 'Jun', 'Wren', 'Sol', 'Pip'])}"
    return StoryParams(setting=setting, hero_name=hero_name, hero_type=hero_type, trait=trait, detective_name=detective_name)


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def asp_valid_settings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery_valid/1."))
    return sorted(set(asp.atoms(model, "mystery_valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_settings()
        print(f"{len(vals)} compatible settings:\n")
        for (sid,) in vals:
            print(f"  {sid}")
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
            header = f"### {p.hero_name}: {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
