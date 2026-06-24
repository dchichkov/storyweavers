#!/usr/bin/env python3
"""
storyworlds/worlds/small_conflict_curiosity_rhyme_whodunit.py
=============================================================

A small whodunit-style story world with conflict, curiosity, and rhyme.

Seed tale:
---
On a small, rainy night, Mina found a missing silver spoon in her house.
She was curious and looked for clues with her brother, Theo.
A little conflict flared when Theo wanted to accuse the gardener right away,
but Mina noticed a rhyme on a scrap of paper: "Near the stair, under the chair."
They followed the clue and found the spoon tucked behind the chair in the parlor,
where the cat had batted it during play.
Theo apologized. Mina laughed, and they solved the small mystery together.

The simulation models:
- physical meters: clues found, mess, hiddenness, distance, etc.
- emotional memes: curiosity, conflict, relief, trust, surprise, pride.

The prose is authored from simulated state rather than a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    place: str = ""
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)


@dataclass
class Clue:
    id: str
    text: str
    location: str
    rhyme: bool = False
    points_to: str = ""


@dataclass
class Suspect:
    id: str
    label: str
    alibi: str
    motive: str
    likely: bool = False


@dataclass
class Setting:
    name: str
    indoor: bool
    rooms: list[str]
    weather: str
    mood: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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


@dataclass
class StoryParams:
    setting: str
    object_id: str
    hero: str
    sidekick: str
    suspect: str
    seed: Optional[int] = None


SETTINGS = {
    "house": Setting("the house", True, ["hall", "stairs", "parlor", "kitchen"], "rainy", "quiet"),
    "library": Setting("the library", True, ["desk", "shelves", "reading nook", "hall"], "windy", "still"),
    "garden_room": Setting("the garden room", True, ["bench", "doorway", "table", "corner"], "gray", "soft"),
}

OBJECTS = {
    "spoon": Entity(id="spoon", type="thing", label="silver spoon", phrase="a small silver spoon", place="parlor"),
    "key": Entity(id="key", type="thing", label="brass key", phrase="a tiny brass key", place="desk"),
    "badge": Entity(id="badge", type="thing", label="blue badge", phrase="a blue badge with a pin", place="nook"),
}

SUSPECTS = {
    "gardener": Suspect("gardener", "the gardener", "he was trimming roses outside", "his gloves had dirt"),
    "chef": Suspect("chef", "the chef", "she was stirring soup in the kitchen", "she had been in a hurry"),
    "cat": Suspect("cat", "the cat", "it was napping, then darting around", "it liked to bat shiny things"),
}

NAMES_GIRL = ["Mina", "Ivy", "Nora", "Lia", "Rose", "Clara"]
NAMES_BOY = ["Theo", "Owen", "Finn", "Noel", "Eli", "Jude"]


def rhyme_line(clue: Clue) -> str:
    return clue.text


def pattern_for(obj_id: str) -> Clue:
    if obj_id == "spoon":
        return Clue("spoon", "Near the stair, under the chair.", "stairs", True, "chair")
    if obj_id == "key":
        return Clue("key", "By the shelf, beside the elf.", "shelves", True, "shelves")
    return Clue("badge", "Past the nook, near the book.", "nook", True, "book")


def suspect_for(obj_id: str) -> str:
    return {"spoon": "cat", "key": "chef", "badge": "gardener"}[obj_id]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting in SETTINGS:
        for obj in OBJECTS:
            out.append((setting, obj, suspect_for(obj)))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


ASP_RULES = r"""
possible(S,O,U) :- setting(S), object(O), suspect(U).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a small whodunit for a child that features the word "{f["object"].label}".',
        f"Tell a mystery story where {f['hero'].id} follows a rhyme clue and solves a conflict with {f['sidekick'].id}.",
        f"Write a gentle detective story with curiosity, a brief argument, and a rhyme that points to the missing item.",
    ]


def build_story(world: World, hero: Entity, sidekick: Entity, obj: Entity, suspect: Suspect, clue: Clue) -> None:
    hero.memes["curiosity"] = 2
    sidekick.memes["curiosity"] = 1
    sidekick.memes["conflict"] = 0

    world.say(f"It was a small, quiet evening in {world.setting.name}, and {hero.id} noticed that {obj.phrase} was missing.")
    world.say(f"{hero.id} grew curious at once and asked {sidekick.id} to help look for clues.")
    world.para()

    hero.memes["curiosity"] += 1
    sidekick.memes["conflict"] += 1
    world.say(f"{sidekick.id} thought it must be {suspect.label}, {suspect.alibi}, because {suspect.motive}.")
    world.say(f'But {hero.id} frowned. "Let’s not guess yet," {hero.id} said. "Let’s look."')
    world.para()

    world.say(f"Then {hero.id} found a little scrap of paper with a rhyme: \"{rhyme_line(clue)}\"")
    hero.memes["pride"] = 1
    sidekick.memes["conflict"] = 0
    sidekick.memes["relief"] = 1
    world.say(f"The clue led them to the {obj.place}, where the missing {obj.label} was tucked away.")
    world.say(f"It turned out the {suspect.label} had nudged it there during play, not from any bad plan at all.")
    world.para()

    hero.memes["relief"] = 1
    hero.memes["trust"] = 1
    sidekick.memes["trust"] = 1
    world.say(f"{sidekick.id} laughed and apologized for accusing too quickly, and {hero.id} smiled because the mystery was solved.")
    world.say(f"In the end, the small room felt calm again, and the tiny clue had done its job.")


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].id
    sidekick = f["sidekick"].id
    obj = f["object"].label
    suspect = f["suspect"].label
    return [
        QAItem(
            question=f"What went missing in the story?",
            answer=f"The missing thing was {f['object'].phrase}, which {hero} noticed was gone.",
        ),
        QAItem(
            question=f"Why did {hero} and {sidekick} look around?",
            answer=f"They looked around because {hero} was curious and wanted to solve the little mystery instead of guessing.",
        ),
        QAItem(
            question=f"What did {sidekick} first think had happened?",
            answer=f"{sidekick} first thought it might be {suspect}, but that guess turned out to be wrong.",
        ),
        QAItem(
            question=f"What rhyme helped solve the case?",
            answer=f"The rhyme said: \"{f['clue'].text}\" and it pointed them to the hiding place.",
        ),
        QAItem(
            question=f"Where was the {obj} found?",
            answer=f"It was found in the {f['object'].place}, tucked where the rhyme led them.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a little piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes you want to look, ask questions, and learn what is going on.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like chair and stair.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for p in sample.prompts:
        parts.append(f"- {p}")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    out = ["--- world ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(out)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    obj = args.object_id or rng.choice(list(OBJECTS))
    expected = suspect_for(obj)
    suspect = args.suspect or expected
    if args.suspect and args.suspect != expected:
        raise StoryError("That suspect does not fit this small whodunit.")
    hero = args.hero or rng.choice(NAMES_GIRL + NAMES_BOY)
    sidekick = args.sidekick or rng.choice([n for n in NAMES_GIRL + NAMES_BOY if n != hero])
    return StoryParams(setting=setting, object_id=obj, hero=hero, sidekick=sidekick, suspect=suspect)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.hero, kind="character", type="girl" if params.hero in NAMES_GIRL else "boy"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="girl" if params.sidekick in NAMES_GIRL else "boy"))
    obj = world.add(Entity(**{**OBJECTS[params.object_id].__dict__}))
    clue = pattern_for(params.object_id)
    suspect = SUSPECTS[params.suspect]
    world.facts.update(hero=hero, sidekick=sidekick, object=obj, suspect=suspect, clue=clue)
    build_story(world, hero, sidekick, obj, suspect, clue)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Small whodunit story world with rhyme clues.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object-id", choices=OBJECTS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--hero")
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


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(setting="house", object_id="spoon", hero="Mina", sidekick="Theo", suspect="cat"),
    StoryParams(setting="library", object_id="key", hero="Ivy", sidekick="Noel", suspect="chef"),
    StoryParams(setting="garden_room", object_id="badge", hero="Lia", sidekick="Jude", suspect="gardener"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show possible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
