#!/usr/bin/env python3
"""
storyworlds/worlds/neologism_sharing_folk_tale.py
=================================================

A standalone storyworld about a small folk-tale-style act of sharing, where a
new word is coined, tested, and gently carried through the village.

Premise:
- A child or villager invents a neologism for a useful shared thing.
- The word begins to travel because the thing itself is shared.
- A small tension appears when someone misunderstands the new word.
- The tale resolves when the group shares both the object and the meaning.

This world is intentionally tiny and classical: the state changes are simple,
physical meters and emotional memes drive the prose, and the ending proves what
changed.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    possessed_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    object_kind: str
    object_label: str
    neologism: str
    seed: Optional[int] = None


PLACES = {
    "village_green": "the village green",
    "well": "the old well",
    "market_path": "the market path",
    "hill": "the little hill",
}

HERO_NAMES = ["Mira", "Tobin", "Lina", "Jon", "Sera", "Pip"]
HELPER_NAMES = ["Grandma", "Uncle", "Rowan", "Bram", "Auntie", "Old Nan"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["woman", "man", "woman", "man", "woman", "woman"]

OBJECTS = [
    ("cup", "a wooden cup"),
    ("blanket", "a warm blanket"),
    ("basket", "a round basket"),
    ("ladle", "a little ladle"),
]


class StoryWorld:
    def __init__(self, place: str):
        self.world = World(place)

    def render(self) -> str:
        return self.world.render()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def child_name(rng: random.Random, gender: str) -> str:
    if gender == "girl":
        return rng.choice(["Mira", "Lina", "Sera", "Pip"])
    return rng.choice(["Tobin", "Jon", "Bram", "Pip"])


def helper_name(rng: random.Random) -> str:
    return rng.choice(HELPER_NAMES)


def object_for_place(rng: random.Random) -> tuple[str, str]:
    return rng.choice(OBJECTS)


def title_case_word(w: str) -> str:
    return w[:1].upper() + w[1:]


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    item = world.add(Entity(id="shared_item", type=params.object_kind, label=params.object_kind,
                            phrase=params.object_label, owner=helper.id))

    # State: who has the object, how widely the word has spread, how understood it is.
    hero.memes["curiosity"] = 1
    helper.memes["warmth"] = 1
    item.meters["shared"] = 0
    world.facts["neologism"] = params.neologism

    world.say(
        f"Long ago, at {params.place}, there lived a little {params.hero_type} named {params.hero_name} "
        f"who loved to listen for new words."
    )
    world.say(
        f"One bright morning, {params.helper_name} brought out {params.object_label} and smiled, "
        f"for there was not enough for one pair of hands, so it had to be shared."
    )
    world.say(
        f"{params.hero_name} looked at the thing and said, "
        f"'{title_case_word(params.neologism)}!' "
        f"It was a new word for passing something kindly from one person to another."
    )

    world.para()
    hero.memes["hope"] = 1
    item.meters["shared"] += 1
    item.possessed_by = hero.id
    world.say(
        f"{params.helper_name} laughed, because the new word fit the moment, and {params.helper_name} let {params.hero_name} "
        f"hold {item.phrase} first."
    )
    world.say(
        f"{params.hero_name} carried it carefully, and the little word began to travel with the object."
    )

    world.para()
    helper.memes["confusion"] = 1
    hero.memes["worry"] = 1
    world.say(
        f"But then a passing neighbor frowned and asked what {title_case_word(params.neologism)} meant."
    )
    world.say(
        f"{params.hero_name} nearly lost the thread of the tale, for a new word can sound strange before it is loved."
    )

    world.para()
    item.meters["shared"] += 1
    helper.memes["kindness"] = 1
    hero.memes["joy"] = 1
    world.say(
        f"So {params.helper_name} showed the meaning by sharing again: first the object, then a smile, then the turn to hold it next."
    )
    world.say(
        f"The neighbor nodded, and soon everyone on {params.place} was using {title_case_word(params.neologism)} for the gentle passing of {params.object_label}."
    )

    world.para()
    item.possessed_by = None
    hero.memes["pride"] = 1
    helper.memes["pride"] = 1
    world.say(
        f"By evening, the {params.object_kind} had moved from hand to hand, but nobody felt poorer for it."
    )
    world.say(
        f"The new word was no longer strange. It had become part of the village music, and {params.hero_name} went home smiling, "
        f"happy that sharing could make both a thing and a word grow brighter."
    )

    world.facts.update(hero=hero, helper=helper, item=item)
    return world


# ---------------------------------------------------------------------------
# Registries and ASP twin
# ---------------------------------------------------------------------------
PLACES_REGISTRY = {
    "village_green": PLACES["village_green"],
    "well": PLACES["well"],
    "market_path": PLACES["market_path"],
    "hill": PLACES["hill"],
}

OBJECT_REGISTRY = {
    "cup": "a wooden cup",
    "blanket": "a warm blanket",
    "basket": "a round basket",
    "ladle": "a little ladle",
}

NEOLOGISMS = [
    "glimmershare",
    "handfolk",
    "passlet",
    "warmling",
    "kindstep",
    "shareling",
]

ASP_RULES = r"""
valid_story(P, O, N) :- place(P), object(O), neologism(N).
share_story(P, O, N) :- valid_story(P, O, N), shareable(O).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES_REGISTRY:
        lines.append(asp.fact("place", pid))
    for oid in OBJECT_REGISTRY:
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("shareable", oid))
    for neo in NEOLOGISMS:
        lines.append(asp.fact("neologism", neo))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, o, n) for p in PLACES_REGISTRY for o in OBJECT_REGISTRY for n in NEOLOGISMS}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} story combinations).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(python_set - clingo_set))
    print("only in asp:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES_REGISTRY:
        for obj in OBJECT_REGISTRY:
            for neo in NEOLOGISMS:
                combos.append((place, obj, neo))
    return combos


def explain_invalid() -> str:
    return "(No story: the request does not describe a coherent sharing tale.)"


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story for a young child about sharing a {f["item"].phrase} and coining the word "{f["neologism"]}".',
        f"Tell a gentle village story where {f['hero'].id} invents a new word for sharing and the meaning spreads by example.",
        f"Write a short folk tale about a new word, a shared object, and a small misunderstanding that ends kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    neo = f["neologism"]
    return [
        QAItem(
            question=f"What new word did {hero.id} say for sharing {item.phrase}?",
            answer=f"{hero.id} said '{title_case_word(neo)}' as a new word for sharing {item.phrase}.",
        ),
        QAItem(
            question=f"Who helped show what {title_case_word(neo)} meant?",
            answer=f"{helper.id} helped by sharing {item.phrase} again and letting the meaning be seen by example.",
        ),
        QAItem(
            question=f"What happened to the {item.label} by the end?",
            answer=f"The {item.label} was passed from hand to hand, so it became shared instead of belonging to only one person.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a neologism?",
            answer="A neologism is a brand-new word or phrase that people have just made up.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, hold, or enjoy something too.",
        ),
        QAItem(
            question="Why do folk tales often repeat important words?",
            answer="Folk tales often repeat important words so listeners can remember them and pass them along.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes} owner={e.owner}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about sharing and a new word.")
    ap.add_argument("--place", choices=PLACES_REGISTRY)
    ap.add_argument("--object", dest="object_kind", choices=OBJECT_REGISTRY)
    ap.add_argument("--neologism", choices=NEOLOGISMS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(PLACES_REGISTRY))
    obj = args.object_kind or rng.choice(list(OBJECT_REGISTRY))
    neo = args.neologism or rng.choice(NEOLOGISMS)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or child_name(rng, gender)
    helper = args.helper or helper_name(rng)
    helper_type = rng.choice(["woman", "man"])
    return StoryParams(
        place=place,
        hero_name=name,
        hero_type=gender,
        helper_name=helper,
        helper_type=helper_type,
        object_kind=obj,
        object_label=OBJECT_REGISTRY[obj],
        neologism=neo,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{p} {o} {n}" for p, o, n in asp_valid_stories()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES_REGISTRY:
            for obj in OBJECT_REGISTRY:
                for neo in NEOLOGISMS[:2]:
                    params = StoryParams(
                        place=place,
                        hero_name="Mira",
                        hero_type="girl",
                        helper_name="Grandma",
                        helper_type="woman",
                        object_kind=obj,
                        object_label=OBJECT_REGISTRY[obj],
                        neologism=neo,
                    )
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
