#!/usr/bin/env python3
"""
cinema_twist_reconciliation_magic_adventure.py
==============================================

A small story world about a child at the cinema, where a planned adventure
gets a twist, a little magic helps, and a reconciliation turns the ending warm.
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
class Character:
    id: str
    role: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        if self.role in {"girl", "mother", "woman"}:
            return "she"
        if self.role in {"boy", "father", "man"}:
            return "he"
        return "they"

    def obj(self) -> str:
        if self.role in {"girl", "mother", "woman"}:
            return "her"
        if self.role in {"boy", "father", "man"}:
            return "him"
        return "them"

    def poss(self) -> str:
        if self.role in {"girl", "mother", "woman"}:
            return "her"
        if self.role in {"boy", "father", "man"}:
            return "his"
        return "their"


@dataclass
class Place:
    name: str = "the cinema"
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class ReconciliationGear:
    id: str
    label: str
    magic_kind: str
    helps_with: str
    phrase: str


@dataclass
class StoryParams:
    place: str
    magic_kind: str
    twist_kind: str
    resolution_kind: str
    name: str
    role: str
    companion_name: str
    companion_role: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Character] = {}
        self.history: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, c: Character) -> Character:
        self.entities[c.id] = c
        return c

    def get(self, cid: str) -> Character:
        return self.entities[cid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.history = list(self.history)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

NAMES_GIRL = ["Maya", "Lily", "Nina", "Ava", "Zoe", "Ivy", "Ella", "Mila"]
NAMES_BOY = ["Leo", "Noah", "Finn", "Max", "Theo", "Sam", "Ben", "Jude"]
COMPANION_GIRL = ["Sofia", "Mia", "Nora", "Ruby", "Lucy"]
COMPANION_BOY = ["Eli", "Jack", "Owen", "Tate", "Finn"]
TRAITS = ["brave", "curious", "cheerful", "spirited", "patient", "lively"]

TWISTS = {
    "lost_ticket": {
        "name": "lost ticket",
        "problem": "the ticket slipped under a seat",
        "line": "Then came a twist: the ticket slipped under a seat and could not be found at first.",
        "effect": "worry",
    },
    "late_popcorn": {
        "name": "late popcorn",
        "problem": "the popcorn bucket tipped and rolled away",
        "line": "Then came a twist: the popcorn bucket tipped and rolled away across the floor.",
        "effect": "frustration",
    },
    "wrong_room": {
        "name": "wrong room",
        "problem": "they stepped toward the wrong theater door",
        "line": "Then came a twist: they stepped toward the wrong theater door and had to pause.",
        "effect": "confusion",
    },
}

MAGICS = {
    "sparkle_map": {
        "name": "sparkle map",
        "help": "the glowing map showed the right door",
        "line": "A tiny magic glow made a sparkle map in the air, and it pointed the way.",
    },
    "moon_coin": {
        "name": "moon coin",
        "help": "the moon coin found the missing ticket",
        "line": "A silver moon coin shimmered, and it helped them spot the missing ticket.",
    },
    "story_whisper": {
        "name": "story whisper",
        "help": "the story whisper calmed everybody down",
        "line": "A soft story whisper floated through the hall, and everybody breathed more slowly.",
    },
}

RESOLUTIONS = {
    "share_seat": {
        "name": "share seat",
        "line": "In the end, they shared a seat, shared the popcorn, and the movie could begin.",
    },
    "say_sorry": {
        "name": "say sorry",
        "line": "In the end, they said sorry to each other, and the small hurt melted away.",
    },
    "work_together": {
        "name": "work together",
        "line": "In the end, they worked together, found the way, and went inside smiling.",
    },
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def story_is_reasonable(twist_key: str, magic_key: str, resolution_key: str) -> bool:
    return twist_key in TWISTS and magic_key in MAGICS and resolution_key in RESOLUTIONS


def explain_invalid(twist_key: str, magic_key: str, resolution_key: str) -> str:
    return (
        f"(No story: invalid combination of twist={twist_key}, "
        f"magic={magic_key}, resolution={resolution_key}.)"
    )


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    world = World(Place())
    hero = world.add(Character(id=params.name, role=params.role))
    companion = world.add(Character(id=params.companion_name, role=params.companion_role))
    world.facts.update(hero=hero, companion=companion)
    return world


def open_story(world: World, params: StoryParams) -> None:
    hero: Character = world.facts["hero"]  # type: ignore[assignment]
    companion: Character = world.facts["companion"]  # type: ignore[assignment]
    world.say(
        f"{hero.id} was a {params.role} who loved adventure, especially on movie day at the cinema."
    )
    world.say(
        f"{hero.pronoun().capitalize()} went with {companion.id}, {companion.poss()} {companion.role}, "
        f"to see a story full of wonder."
    )
    world.say(
        f"{hero.id} had a bright heart for magic, and the cinema lights felt like the start of a quest."
    )


def introduce_twist(world: World, params: StoryParams) -> None:
    twist = TWISTS[params.twist_kind]
    hero: Character = world.facts["hero"]  # type: ignore[assignment]
    world.say(twist["line"])
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    if params.twist_kind == "lost_ticket":
        hero.memes["panic"] = hero.memes.get("panic", 0.0) + 1.0
    elif params.twist_kind == "late_popcorn":
        hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1.0
    else:
        hero.memes["confusion"] = hero.memes.get("confusion", 0.0) + 1.0


def use_magic(world: World, params: StoryParams) -> None:
    magic = MAGICS[params.magic_kind]
    hero: Character = world.facts["hero"]  # type: ignore[assignment]
    companion: Character = world.facts["companion"]  # type: ignore[assignment]
    world.say(magic["line"])
    hero.meters["magic"] = hero.meters.get("magic", 0.0) + 1.0
    companion.meters["magic"] = companion.meters.get("magic", 0.0) + 1.0
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0


def reconcile(world: World, params: StoryParams) -> None:
    hero: Character = world.facts["hero"]  # type: ignore[assignment]
    companion: Character = world.facts["companion"]  # type: ignore[assignment]
    if params.resolution_kind == "say_sorry":
        world.say(
            f"{hero.id} looked at {companion.id} and said sorry for getting so fussy."
        )
        world.say(
            f"{companion.id} said sorry too, because the twist had made everyone jumpy."
        )
    elif params.resolution_kind == "share_seat":
        world.say(
            f"{hero.id} and {companion.id} moved closer and shared the seat, the snack, and the calm."
        )
    else:
        world.say(
            f"{hero.id} and {companion.id} took a breath, held hands, and worked together."
        )
    hero.memes["reconciliation"] = 1.0
    companion.memes["reconciliation"] = 1.0
    hero.memes["worry"] = 0.0
    companion.memes["worry"] = 0.0


def ending(world: World, params: StoryParams) -> None:
    hero: Character = world.facts["hero"]  # type: ignore[assignment]
    companion: Character = world.facts["companion"]  # type: ignore[assignment]
    world.say(
        f"In the end, {hero.id} felt close to {companion.id} again, and the cinema glowed like a happy promise."
    )
    world.say(
        f"{hero.pronoun().capitalize()} watched the screen with a calm smile, ready for the adventure to begin."
    )


def simulate(params: StoryParams) -> World:
    world = setup_world(params)
    open_story(world, params)
    world.para()
    introduce_twist(world, params)
    use_magic(world, params)
    world.para()
    reconcile(world, params)
    ending(world, params)
    world.facts.update(params=params)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f'Write a child-friendly adventure story at the cinema that includes "{p.magic_kind}" and a surprising twist.',
        f"Tell a gentle movie-day story where {p.name} faces a {p.twist_kind.replace('_', ' ')} but a little magic helps.",
        f"Write a short story about two friends at the cinema who have a twist, use magic, and reconcile at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    hero: Character = world.facts["hero"]  # type: ignore[assignment]
    companion: Character = world.facts["companion"]  # type: ignore[assignment]
    twist = TWISTS[p.twist_kind]["name"]
    magic = MAGICS[p.magic_kind]["name"]
    resolution = RESOLUTIONS[p.resolution_kind]["name"]
    return [
        QAItem(
            question=f"Where did {hero.id} go for the adventure?",
            answer=f"{hero.id} went to the cinema with {companion.id} for an adventure story.",
        ),
        QAItem(
            question=f"What twist happened during the movie day?",
            answer=f"The story had a {twist} twist, which made things tricky for a little while.",
        ),
        QAItem(
            question=f"How did magic help in the story?",
            answer=f"The {magic} helped the children move from worry to calm and made the problem easier to solve.",
        ),
        QAItem(
            question=f"What ended the trouble between {hero.id} and {companion.id}?",
            answer=f"They used {resolution} and ended the story feeling close again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cinema?",
            answer="A cinema is a place where people go to watch movies on a big screen.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a disagreement or a hurt feeling.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something wonderful and surprising that can help characters in a special way.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid if it has a known twist, known magic, and known resolution.
valid_story(T, M, R) :- twist(T), magic(M), resolution(R).

% The story includes a reconciliation when the resolution is a peace-making ending.
reconciles(R) :- resolution(R).

% A magic choice is helpful if it can support a twist and still lead to reconciliation.
helpful(M) :- magic(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k in TWISTS:
        lines.append(asp.fact("twist", k))
    for k in MAGICS:
        lines.append(asp.fact("magic", k))
    for k in RESOLUTIONS:
        lines.append(asp.fact("resolution", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set((t, m, r) for t in TWISTS for m in MAGICS for r in RESOLUTIONS if story_is_reasonable(t, m, r))
    asp_set = set(asp_valid_stories())
    if asp_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(asp_set)} combinations).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cinema story world: twist, magic, and reconciliation.")
    ap.add_argument("--place", default="cinema", choices=["cinema"])
    ap.add_argument("--twist-kind", choices=sorted(TWISTS))
    ap.add_argument("--magic-kind", choices=sorted(MAGICS))
    ap.add_argument("--resolution-kind", choices=sorted(RESOLUTIONS))
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["girl", "boy"], default=None)
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-role", choices=["girl", "boy"], default=None)
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
    twist = args.twist_kind or rng.choice(list(TWISTS))
    magic = args.magic_kind or rng.choice(list(MAGICS))
    resolution = args.resolution_kind or rng.choice(list(RESOLUTIONS))
    if not story_is_reasonable(twist, magic, resolution):
        raise StoryError(explain_invalid(twist, magic, resolution))
    role = args.role or rng.choice(["girl", "boy"])
    comp_role = args.companion_role or ("boy" if role == "girl" else "girl")
    name = args.name or rng.choice(NAMES_GIRL if role == "girl" else NAMES_BOY)
    comp = args.companion_name or rng.choice(COMPANION_GIRL if comp_role == "girl" else COMPANION_BOY)
    if comp == name:
        comp = rng.choice([n for n in (COMPANION_GIRL if comp_role == "girl" else COMPANION_BOY) if n != name])
    return StoryParams(
        place="cinema",
        magic_kind=magic,
        twist_kind=twist,
        resolution_kind=resolution,
        name=name,
        role=role,
        companion_name=comp,
        companion_role=comp_role,
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
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


CURATED = [
    StoryParams(
        place="cinema",
        magic_kind="sparkle_map",
        twist_kind="wrong_room",
        resolution_kind="work_together",
        name="Maya",
        role="girl",
        companion_name="Eli",
        companion_role="boy",
    ),
    StoryParams(
        place="cinema",
        magic_kind="moon_coin",
        twist_kind="lost_ticket",
        resolution_kind="say_sorry",
        name="Leo",
        role="boy",
        companion_name="Nora",
        companion_role="girl",
    ),
    StoryParams(
        place="cinema",
        magic_kind="story_whisper",
        twist_kind="late_popcorn",
        resolution_kind="share_seat",
        name="Ava",
        role="girl",
        companion_name="Finn",
        companion_role="boy",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible story combinations:\n")
        for t, m, r in triples:
            print(f"  twist={t:12} magic={m:12} resolution={r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name} at the cinema"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
