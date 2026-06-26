#!/usr/bin/env python3
"""
A small folk-tale storyworld about a kindness quest and a gentle transformation.

Premise:
- A cheerful child or small creature hears of a quest.
- They travel through a simple setting to help someone in need.
- A kind act brings about a transformation.
- The ending proves the world changed.

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
# Core world model
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
    holds: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"travel": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"hope": 0.0, "joy": 0.0, "kindness": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_plural(self) -> bool:
        return self.type in {"villagers", "children"}

    def they(self) -> str:
        return "them" if self.is_plural() else "it"


@dataclass
class Place:
    id: str
    name: str
    kind: str
    description: str
    paths: set[str] = field(default_factory=set)
    holds: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    item: str
    receiver: str
    transform: str
    required_kindness: float = 1.0


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.logs.append(text)

    def render(self) -> str:
        return " ".join(self.logs)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "forest": Place(
        id="forest",
        name="the whispering forest",
        kind="forest",
        description="Tall trees leaned together, and little birds kept watch from the boughs.",
        paths={"clearing", "river", "hill"},
        holds={"mushroom", "lantern", "berry"},
    ),
    "village": Place(
        id="village",
        name="the old village",
        kind="village",
        description="Small houses stood shoulder to shoulder, and smoke curled up like ribbons.",
        paths={"well", "bakery", "bridge"},
        holds={"bread", "lamp", "key"},
    ),
    "hill": Place(
        id="hill",
        name="the green hill",
        kind="hill",
        description="Grass rolled in soft waves, and the wind hummed over the tops of the stones.",
        paths={"oak", "spring", "path"},
        holds={"flower", "cloak", "horn"},
    ),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        title="bring the lost lantern home",
        item="a lost lantern",
        receiver="the widow at the cottage",
        transform="the lantern glowed bright again",
    ),
    "flower": Quest(
        id="flower",
        title="find the silver flower",
        item="a silver flower",
        receiver="the sleeping prince",
        transform="the prince woke with a smile",
    ),
    "bread": Quest(
        id="bread",
        title="carry fresh bread across the hill",
        item="a warm loaf of bread",
        receiver="the hungry goat-child",
        transform="the goat-child grew full and cheerful",
    ),
}

NAMES = ["Mila", "Nora", "Tobin", "Perry", "Anya", "Soren", "Lena", "Hugo"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["mouse", "fox", "owl", "old woman", "small dog"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, quest: str) -> bool:
    if place == "forest":
        return quest in {"lantern", "flower"}
    if place == "village":
        return quest in {"lantern", "bread"}
    if place == "hill":
        return quest in {"flower", "bread"}
    return False


def valid_combos() -> list[tuple[str, str]]:
    return [(p, q) for p in PLACES for q in QUESTS if valid_combo(p, q)]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place=place)

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, label=params.helper))
    quest = QUESTS[params.quest]
    prize = world.add(Entity(id="quest_item", type="treasure", label=quest.item, phrase=quest.item, owner=hero.id))
    receiver = world.add(Entity(id="receiver", kind="character", type="elder", label=quest.receiver))

    world.facts.update(hero=hero, helper=helper, quest=quest, prize=prize, receiver=receiver, place=place)

    world.say(f"Once, in {place.name}, {hero.id} was a little {hero.type} who kept a bright heart.")
    world.say(f"{hero.id} felt overjoyed to walk under the trees and enthuse about every tiny track in the dirt.")
    world.say(f"One morning, {helper.id} met {hero.id} by the path and spoke of a quest: {quest.title}.")
    world.say(f"The two of them listened, and {hero.id} promised to help because {hero.pronoun('subject')} loved kindness more than comfort.")
    world.say(f"They set off together, past {place.description.lower()}")

    hero.meters["travel"] += 1
    hero.memes["hope"] += 1
    hero.memes["kindness"] += 1
    helper.memes["hope"] += 1

    if quest.id == "lantern":
        world.say("They searched under roots and behind stones until they found the lost lantern hanging in a thorn bush.")
        world.say(f"{hero.id} carried it carefully to {quest.receiver}, and the old room filled with warm gold light.")
    elif quest.id == "flower":
        world.say("They climbed the hill where the silver flower grew beside a stone cup of rain.")
        world.say(f"{hero.id} picked it with gentle fingers, and when it reached {quest.receiver}, {quest.transform}.")
    elif quest.id == "bread":
        world.say("They crossed the wind-swept road with the warm loaf wrapped in cloth.")
        world.say(f"{hero.id} shared it with {quest.receiver}, and {quest.transform}.")

    hero.memes["joy"] += 2
    helper.memes["joy"] += 1
    hero.memes["kindness"] += 1

    transformed = Entity(
        id="transformed",
        kind="thing",
        type="blessing",
        label="a kinder world",
        phrase="a kinder world",
    )
    world.add(transformed)

    world.say(f"Because {hero.id} chose kindness, the day itself seemed to change.")
    world.say(f"When the quest was done, {hero.id} was still a small child, but {hero.pronoun('possessive')} heart felt larger, and everyone near {hero.id} seemed changed too.")
    world.say(f"In the end, {hero.id} went home overjoyed, while {helper.id} walked beside {hero.pronoun('object')} with a happy, quiet smile.")

    world.facts["transformed"] = transformed
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    place = f["place"]
    return [
        f"Write a short folk tale about {hero.id} in {place.name} who goes on a kindness quest.",
        f"Tell a child-friendly story where someone overjoyed decides to enthuse about helping others.",
        f"Write a simple story in which a small hero completes {quest.title} and the ending shows a transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    quest: Quest = f["quest"]
    place: Place = f["place"]
    receiver: Entity = f["receiver"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type} in {place.name}, and {helper.id}, who came with {hero.pronoun('object')} on the quest.",
        ),
        QAItem(
            question=f"What quest did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {quest.title}. That quest was a kind one, because it helped {receiver.label}.",
        ),
        QAItem(
            question=f"Why did the ending feel different from the beginning?",
            answer=f"The ending felt different because {hero.id} chose kindness and finished the quest, so {quest.transform}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel during the story?",
            answer=f"{hero.id} felt overjoyed at the start, and that happy feeling helped {hero.pronoun('object')} enthuse about the journey and keep going.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest in a folk tale?",
            answer="A quest is a special journey with a purpose, like finding something, helping someone, or bringing back a needed gift.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, share, or care for someone else in a gentle way.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state to another, like a sad day turning bright or a worried heart becoming brave.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_combo(Place, Quest) :- place(Place), quest(Quest), allowed(Place, Quest).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for q in sorted(p.paths):
            lines.append(asp.fact("path", pid, q))
        for h in sorted(p.holds):
            lines.append(asp.fact("holds", pid, h))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for place, quest in valid_combos():
        lines.append(asp.fact("allowed", place, quest))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld: a kindness quest and a transformation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = valid_combos()
    if args.place and args.quest and not valid_combo(args.place, args.quest):
        raise StoryError("That quest does not fit that place in this small folk tale.")
    filtered = [c for c in choices if (args.place is None or c[0] == args.place) and (args.quest is None or c[1] == args.quest)]
    if not filtered:
        raise StoryError("No valid story combination matches the given options.")
    place, quest = rng.choice(sorted(filtered))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    return StoryParams(place=place, quest=quest, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type)


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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest) combos:")
        for place, quest in combos:
            print(f"  {place:8} {quest}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, quest in valid_combos():
            params = StoryParams(
                place=place,
                quest=quest,
                hero=random.Random(base_seed + len(samples)).choice(NAMES),
                hero_type=random.Random(base_seed + len(samples) + 1).choice(HERO_TYPES),
                helper=random.Random(base_seed + len(samples) + 2).choice(NAMES),
                helper_type=random.Random(base_seed + len(samples) + 3).choice(HELPER_TYPES),
                seed=base_seed + len(samples),
            )
            if params.helper == params.hero:
                params.helper = next(n for n in NAMES if n != params.hero)
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
