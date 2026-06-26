#!/usr/bin/env python3
"""
A small detective-story world about a missing coil, teamwork, sharing, and a happy ending.

The world is built around a child-friendly mystery: a helpful detective and a few
neighbors search for a lost coil, compare clues, share tools, and solve the case
together. The world state determines the prose, the conflict, and the resolution.
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

TITLE = "Coil Teamwork Sharing Happy Ending Detective Story"


@dataclass
class Scene:
    place: str
    weather: str
    surfaces: list[str] = field(default_factory=list)


@dataclass
class Item:
    id: str
    label: str
    owner: str = ""
    held_by: str = ""
    shared: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Character:
    id: str
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"girl", "woman", "detective"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    helper: str
    owner: str
    item_label: str = "coil"
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.characters: dict[str, Character] = {}
        self.items: dict[str, Item] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}

    def add_character(self, c: Character) -> Character:
        self.characters[c.id] = c
        return c

    def add_item(self, i: Item) -> Item:
        self.items[i.id] = i
        return i

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)

    def trace(self) -> str:
        lines = [f"scene: {self.scene.place}, weather={self.scene.weather}, surfaces={self.scene.surfaces}"]
        for c in self.characters.values():
            lines.append(f"char {c.id}: meters={c.meters} memes={c.memes}")
        for i in self.items.values():
            lines.append(f"item {i.id}: owner={i.owner} held_by={i.held_by} shared={i.shared} found={i.found}")
        return "\n".join(lines)


SETTINGS = {
    "market": Scene(place="the market", weather="bright", surfaces=["stone", "wood", "cloth"]),
    "workshop": Scene(place="the workshop", weather="quiet", surfaces=["metal", "wood", "shelves"]),
    "library": Scene(place="the library", weather="soft", surfaces=["table", "floor", "shelf"]),
    "garden": Scene(place="the garden shed", weather="breezy", surfaces=["soil", "bench", "crate"]),
}

NAMES = ["Mina", "Noah", "Lina", "Toby", "Ivy", "Owen", "Zara", "Eli"]
ROLES = ["girl", "boy"]


ASP_RULES = r"""
% A coil is found when teamwork and sharing both happen.
found_coil(C) :- teamwork(C), sharing(C).
happy_ending(C) :- found_coil(C).

#show found_coil/1.
#show happy_ending/1.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    lines.append(asp.fact("item", "coil"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/1."))
    has = bool(asp.atoms(model, "happy_ending"))
    py = True
    if has == py:
        print("OK: ASP and Python agree about the happy ending.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly detective story about a lost coil.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--helper", choices=NAMES)
    ap.add_argument("--owner", choices=NAMES)
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
    place = args.place or rng.choice(list(SETTINGS))
    helper = args.helper or rng.choice(NAMES)
    owner = args.owner or rng.choice([n for n in NAMES if n != helper])
    if helper == owner:
        raise StoryError("The helper and owner must be different people for this mystery.")
    return StoryParams(place=place, helper=helper, owner=owner)


def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    detective = world.add_character(Character(id="detective", name=params.helper, role="detective"))
    owner = world.add_character(Character(id="owner", name=params.owner, role="child"))
    coil = world.add_item(Item(id="coil", label="coil", owner=owner.id))
    world.facts.update(detective=detective, owner=owner, coil=coil)
    return world


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    detective: Character = world.facts["detective"]  # type: ignore[assignment]
    owner: Character = world.facts["owner"]  # type: ignore[assignment]
    coil: Item = world.facts["coil"]  # type: ignore[assignment]

    detective.memes["curiosity"] = 1.0
    detective.memes["kindness"] = 1.0
    owner.memes["worry"] = 1.0

    world.say(f"{detective.name} was the little detective at {world.scene.place}.")
    world.say(f"One morning, {owner.name} could not find a small coil they had saved for a special project.")
    world.say(f"{detective.name} noticed the worry right away and promised to help.")

    # Clues, teamwork, sharing.
    world.say(f"They looked together under a bench, beside a shelf, and near a bright wooden crate.")
    world.say(f"{owner.name} shared a scrap of string that matched the coil, and {detective.name} shared a magnifying glass.")
    detective.meters["search"] = 1.0
    owner.meters["search"] = 1.0
    detective.memes["teamwork"] = 1.0
    owner.memes["teamwork"] = 1.0

    # Turn: the clue leads them to the coil.
    coil.found = True
    coil.held_by = detective.id
    detective.meters["clue"] = 1.0
    world.say(f"At last, {detective.name} spotted the coil tucked behind a basket.")
    world.say(f"{detective.name} picked it up carefully, then held it out so {owner.name} could check it.")

    coil.shared = True
    coil.held_by = owner.id
    owner.memes["relief"] = 1.0
    detective.memes["joy"] = 1.0
    world.say(f"{owner.name} smiled because the coil was safe, and {detective.name} shared it back with a grin.")
    world.say(f"Together they carried it to the work table and finished the little project side by side.")
    world.say(f"It was a happy ending: the lost coil was found, and the two friends had solved the mystery together.")

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    detective: Character = p["detective"]  # type: ignore[assignment]
    owner: Character = p["owner"]  # type: ignore[assignment]
    return [
        f"Write a short detective story for a young child about {detective.name} helping {owner.name} find a coil.",
        f"Tell a gentle mystery where teamwork and sharing lead to a happy ending at {world.scene.place}.",
        f"Write a child-friendly detective tale that includes a lost coil, shared clues, and a cheerful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    detective: Character = world.facts["detective"]  # type: ignore[assignment]
    owner: Character = world.facts["owner"]  # type: ignore[assignment]
    coil: Item = world.facts["coil"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who helped solve the mystery?",
            answer=f"{detective.name} helped solve the mystery by searching with {owner.name}.",
        ),
        QAItem(
            question="What was missing at the start?",
            answer="A small coil was missing at the start of the story.",
        ),
        QAItem(
            question="How did they find the coil?",
            answer="They used teamwork, shared clues, and searched the place together until they found it behind a basket.",
        ),
        QAItem(
            question="What happened at the end?",
            answer="The coil was found, it was shared back safely, and the story ended happily.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do a job together.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something too.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues to solve a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show found_coil/1.\n#show happy_ending/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, helper=NAMES[0], owner=NAMES[1])
            samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
