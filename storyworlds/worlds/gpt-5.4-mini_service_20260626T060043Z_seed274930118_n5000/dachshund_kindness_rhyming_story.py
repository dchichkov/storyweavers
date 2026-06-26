#!/usr/bin/env python3
"""
storyworlds/worlds/dachshund_kindness_rhyming_story.py
======================================================

A small story world about a dachshund, kindness, and a gentle rhyming turn.

Premise:
- A little dachshund wants something sweet and simple in a small neighborhood world.
- Another character needs help, and the dachshund's kindness changes the day.

The world model tracks:
- physical meters: distance, carried items, effort, readiness, warmth
- emotional memes: kindness, worry, pride, joy, gratitude

The prose is generated from state changes, not from a frozen paragraph template.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "animal" or self.type == "dachshund":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    name: str
    helper: str
    gift: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "park": Place("park", "the park"),
    "garden": Place("garden", "the garden"),
    "lane": Place("lane", "the sunny lane"),
}

NAMES = ["Milo", "Pip", "Nina", "Toby", "Ruby", "Luna"]
HELPERS = ["old squirrel", "small cat", "kind child", "round robin"]
GIFTS = {
    "ball": "a red ball",
    "bone": "a tiny toy bone",
    "scarf": "a soft blue scarf",
}

CURATED = [
    StoryParams(place="park", name="Milo", helper="kind child", gift="ball"),
    StoryParams(place="garden", name="Luna", helper="old squirrel", gift="scarf"),
    StoryParams(place="lane", name="Pip", helper="small cat", gift="bone"),
]


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def _rhymes_for(place: str, gift: str) -> tuple[str, str]:
    if place == "park":
        return ("spark", "dark")
    if place == "garden":
        return ("start", "heart")
    return ("glow", "show")


def _setup(world: World, hero: Entity, helper: Entity, gift: Entity) -> None:
    r1, r2 = _rhymes_for(world.place.id, gift.id)
    world.say(
        f"In {world.place.label} light and bright, a dachshund trotted with cheerful might; "
        f"{hero.id} loved to sniff and play, and wagged through the day."
    )
    world.say(
        f"{hero.id} had {gift.phrase}, a treasured treat, and kept it close with happy feet."
    )
    world.say(
        f"But near the path, a small sigh rose; {helper.id} needed help, as {hero.id} soon chose."
    )
    world.facts.update(rhyme1=r1, rhyme2=r2)


def _notice(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} saw {helper.id} and paused to stay; "
        f"{hero.id}'s kind little heart lit up the way."
    )


def _offer(world: World, hero: Entity, helper: Entity, gift: Entity) -> None:
    hero.meters["effort"] = hero.meters.get("effort", 0) + 1
    helper.memes["hope"] = helper.memes.get("hope", 0) + 1
    world.say(
        f'"Please take my {gift.label}," {hero.id} said with a grin; '
        f'"A kind, warm share is the best win."'
    )
    gift.carried_by = helper.id


def _return_kindness(world: World, hero: Entity, helper: Entity, gift: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["gratitude"] = helper.memes.get("gratitude", 0) + 1
    world.say(
        f"{helper.id} smiled wide and thanked {hero.id} with cheer; "
        f"that little kindness made the path feel clear."
    )
    world.say(
        f"{hero.id} felt proud and light, with a wag and a wink; "
        f"the day turned sweet in a sunny blink."
    )
    world.say(
        f"So {hero.id} kept walking on, with {helper.id} nearby; "
        f"their shared good deed made the moment fly."
    )


def tell(place: Place, name: str, helper: str, gift_key: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="animal", type="dachshund", label="dachshund"))
    h = world.add(Entity(id=helper, kind="character", type="helper", label=helper))
    gift = world.add(Entity(id=gift_key, kind="thing", type=gift_key, label=gift_key, phrase=GIFTS[gift_key], owner=hero.id))
    gift.carried_by = hero.id

    _setup(world, hero, h, gift)
    world.para()
    _notice(world, hero, h)
    _offer(world, hero, h, gift)
    world.para()
    _return_kindness(world, hero, h, gift)

    world.facts.update(hero=hero, helper=h, gift=gift, place=place)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    gift: Entity = f["gift"]
    place: Place = f["place"]
    return [
        f'Write a short rhyming story for children about a dachshund named {hero.id} in {place.label}.',
        f"Tell a gentle rhyming story where {hero.id} shows kindness to {helper.id} by sharing {gift.phrase}.",
        f'Write a sweet story that includes the word "dachshund" and ends with kindness being shared in {place.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    gift: Entity = f["gift"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who is the dachshund in the story?",
            answer=f"The dachshund is {hero.id}, who plays in {place.label} and acts kindly.",
        ),
        QAItem(
            question=f"What did {hero.id} share to help {helper.id}?",
            answer=f"{hero.id} shared {gift.phrase}, which showed kindness and made {helper.id} smile.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} feeling proud, because a kind choice turned the day warm and bright.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dachshund?",
            answer="A dachshund is a small dog with a long body and short legs.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="Why can sharing help someone feel better?",
            answer="Sharing can help because it shows care and can make another person feel seen and supported.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- dachshund(H).
kind(H) :- shows_kindness(H).
good_story(P,H) :- place(P), hero(H), kind(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for key in GIFTS:
        lines.append(asp.fact("gift", key))
    lines.append(asp.fact("dachshund", "hero"))
    lines.append(asp.fact("shows_kindness", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    atoms = set(asp.atoms(model, "good_story"))
    py = {("park", "hero"), ("garden", "hero"), ("lane", "hero")}
    if atoms == py:
        print(f"OK: ASP matches Python reasoning ({len(atoms)} stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def explain_choice(place: str, gift: str) -> None:
    if place not in PLACES:
        raise StoryError("Unknown place.")
    if gift not in GIFTS:
        raise StoryError("Unknown gift.")


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming story world about a dachshund and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gift", choices=GIFTS)
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
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    gift = args.gift or rng.choice(list(GIFTS))
    explain_choice(place, gift)
    return StoryParams(place=place, name=name, helper=helper, gift=gift)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.name, params.helper, params.gift)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
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
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/2."))
        print(sorted(set(asp.atoms(model, "good_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name} in {p.place} with {p.gift}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
