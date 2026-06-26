#!/usr/bin/env python3
"""
storyworlds/worlds/china_inner_monologue_surprise_heartwarming.py
=================================================================

A small heartwarming story world set in China, built around a gentle surprise
and an inner monologue that helps a child choose kindness over shyness.

Premise:
- A child is preparing a tiny gift for a grandparent in a busy Chinese market.
- They worry the plan will go wrong.
- A surprise turns out to be a family kindness that makes the child feel brave.
- The ending proves the child changed: they share, speak up, and feel warm inside.

This is a standalone world script that follows the Storyweavers contract.
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
# Small world model
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    atmosphere: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectItem:
    id: str
    label: str
    phrase: str
    type: str
    value: str
    owner_kind: set[str] = field(default_factory=set)
    surprise_kind: str = ""


@dataclass
class StoryParams:
    place: str
    object: str
    hero_name: str
    hero_type: str
    caregiver_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
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
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "market": Place(
        id="market",
        label="a busy market street",
        atmosphere="The air smelled like steamed buns and tea.",
        affords={"buy", "walk", "share"},
    ),
    "home": Place(
        id="home",
        label="a small home kitchen",
        atmosphere="The room was warm and quiet, with a kettle humming softly.",
        affords={"cook", "share", "talk"},
    ),
    "tea_house": Place(
        id="tea_house",
        label="a calm tea house",
        atmosphere="The tables were polished, and the teacups waited in neat rows.",
        affords={"drink", "share", "talk"},
    ),
}

OBJECTS = {
    "dumplings": ObjectItem(
        id="dumplings",
        label="dumplings",
        phrase="a little box of fresh dumplings",
        type="food",
        value="food",
        owner_kind={"grandparent", "caregiver"},
        surprise_kind="shared lunch",
    ),
    "lantern": ObjectItem(
        id="lantern",
        label="lantern",
        phrase="a bright red paper lantern",
        type="decor",
        value="beauty",
        owner_kind={"child", "family"},
        surprise_kind="festival gift",
    ),
    "tea": ObjectItem(
        id="tea",
        label="tea",
        phrase="a wrapped tin of sweet tea",
        type="tea",
        value="comfort",
        owner_kind={"grandparent", "family"},
        surprise_kind="quiet gift",
    ),
    "apples": ObjectItem(
        id="apples",
        label="apples",
        phrase="a bag of shiny apples",
        type="fruit",
        value="care",
        owner_kind={"child", "family"},
        surprise_kind="shared treat",
    ),
}

NAMES_GIRL = ["Mei", "Lin", "Yue", "An", "Ming", "Xiao"]
NAMES_BOY = ["Jun", "Bo", "Wei", "Hao", "Chen", "Tian"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def is_valid_combo(place_id: str, object_id: str) -> bool:
    place = PLACES[place_id]
    obj = OBJECTS[object_id]
    if place_id == "tea_house" and object_id == "lantern":
        return False
    if place_id == "home" and object_id == "dumplings":
        return True
    if place_id == "market" and object_id in {"dumplings", "tea", "apples"}:
        return True
    if place_id == "tea_house" and object_id in {"tea", "apples"}:
        return True
    return False


def valid_combos() -> list[tuple[str, str]]:
    return [(p, o) for p in PLACES for o in OBJECTS if is_valid_combo(p, o)]


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def predict_success(world: World, hero: Entity, item: ObjectItem) -> dict:
    sim = world.copy()
    sim.facts["worry"] = True
    if item.id == "dumplings":
        sim.facts["gift_ready"] = True
        sim.facts["surprise"] = True
    return {
        "kind": item.surprise_kind,
        "softening": True,
    }


def intro(world: World, hero: Entity, caregiver: Entity, item: ObjectItem) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who liked noticing small kind things."
    )
    world.say(
        f"Today, {hero.id} and {hero.pronoun('possessive')} {caregiver.label} went to {world.place.label}."
    )
    world.say(world.place.atmosphere)


def inner_monologue(world: World, hero: Entity, item: ObjectItem) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'Inside, {hero.id} thought, "What if I forget the right words? '
        f'What if {item.label} is not enough?"'
    )
    world.say(
        f'{hero.id} held the {item.label} a little tighter and kept walking.'
    )


def surprise_setup(world: World, caregiver: Entity, hero: Entity, item: ObjectItem) -> None:
    caregiver.memes["secret_kindness"] += 1
    world.say(
        f"Then {caregiver.pronoun().capitalize()} smiled with a secret look, as if {caregiver.pronoun('subject')} knew something gentle."
    )
    world.say(
        f'"I made one more stop earlier," {caregiver.pronoun("subject")} said. '
        f'"You can be the one to give it."'
    )
    world.facts["surprise"] = item.surprise_kind


def reveal(world: World, hero: Entity, caregiver: Entity, item: ObjectItem) -> None:
    hero.memes["surprise"] += 1
    hero.memes["brave"] += 1
    world.say(
        f'{hero.id} blinked in surprise, then felt the worry in {hero.pronoun("possessive")} chest get smaller.'
    )
    world.say(
        f"Now the {item.label} was not just a thing to carry. It was a way to share care."
    )


def ending(world: World, hero: Entity, caregiver: Entity, item: ObjectItem) -> None:
    hero.memes["warmth"] += 1
    world.say(
        f"{hero.id} stood a little taller and gave the gift with both hands."
    )
    world.say(
        f"{caregiver.pronoun().capitalize()} laughed softly, and {hero.id} laughed too. "
        f"The {item.label} felt perfect because it came with love."
    )


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.object not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object}")

    if not is_valid_combo(params.place, params.object):
        raise StoryError("That place and object do not make a believable heartwarming story here.")

    place = PLACES[params.place]
    obj = OBJECTS[params.object]
    world = World(place)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"steps": 0.0},
        memes={"worry": 0.0, "brave": 0.0, "surprise": 0.0, "warmth": 0.0},
    ))
    caregiver = world.add(Entity(
        id="caregiver",
        kind="character",
        type=params.caregiver_type,
        label="grandma" if params.caregiver_type == "grandmother" else "grandpa" if params.caregiver_type == "grandfather" else "caregiver",
        meters={},
        memes={"secret_kindness": 0.0},
    ))
    gift = world.add(Entity(
        id=obj.id,
        kind="thing",
        type=obj.type,
        label=obj.label,
        phrase=obj.phrase,
        owner=hero.id,
        caretaker=caregiver.id,
        meters={"freshness": 1.0},
        memes={},
    ))
    world.facts.update(hero=hero, caregiver=caregiver, gift=gift, obj=obj, place=place)

    intro(world, hero, caregiver, obj)
    world.para()
    inner_monologue(world, hero, obj)
    surprise_setup(world, caregiver, hero, obj)
    reveal(world, hero, caregiver, obj)
    world.para()
    ending(world, hero, caregiver, obj)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obj = f["obj"]
    place = f["place"]
    return [
        f'Write a heartwarming story for a child named {hero.id} in {place.label} with an inner monologue and a surprise.',
        f'Create a gentle story where {hero.id} worries about giving {obj.phrase}, then feels better after a kind surprise.',
        f'Write a short story set in China that includes a quiet thought, a surprise, and a warm ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    caregiver = f["caregiver"]
    gift = f["gift"]
    obj = f["obj"]
    place = f["place"]

    return [
        QAItem(
            question=f"Why was {hero.id} worried at first?",
            answer=(
                f"{hero.id} was worried because {hero.pronoun('subject')} wondered if the words would come out right and if the gift would be enough."
            ),
        ),
        QAItem(
            question=f"What surprise did {caregiver.label} give {hero.id}?",
            answer=(
                f"{caregiver.pronoun().capitalize()} said there had been one more stop earlier and let {hero.id} be the one to give the gift."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} give in the end?",
            answer=(
                f"{hero.id} gave {hero.pronoun('possessive')} {gift.label}, which was {obj.phrase}."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=(
                f"{hero.id} felt brave, warm, and happy because the gift became a way to share care."
            ),
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"The story happened at {place.label}, in a gentle China setting with a cozy, busy feeling.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "tea": [
        QAItem(
            question="What is tea?",
            answer="Tea is a warm drink made by steeping leaves in hot water.",
        ),
        QAItem(
            question="Why do some people share tea with family?",
            answer="People share tea with family because it can be a quiet, caring way to sit together.",
        ),
    ],
    "dumplings": [
        QAItem(
            question="What are dumplings?",
            answer="Dumplings are little pockets of dough that can be filled with meat, vegetables, or other tasty foods.",
        ),
    ],
    "lantern": [
        QAItem(
            question="What is a lantern?",
            answer="A lantern is a light or decoration that can glow or shine and make a room or street look bright.",
        ),
    ],
    "apples": [
        QAItem(
            question="Why are apples a good snack?",
            answer="Apples are crisp and sweet, so they can be a simple and cheerful snack to share.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    obj = world.facts["obj"]
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE.get(obj.id, []))
    out.extend(WORLD_KNOWLEDGE["tea"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
object(O) :- gift(O).

compatible(P,O) :- valid(P,O).
valid(P,O) :- place(P), object(O), afford(P,O), not blocked(P,O).

blocked(tea_house, lantern).

afford(market, dumplings).
afford(market, tea).
afford(market, apples).
afford(home, dumplings).
afford(tea_house, tea).
afford(tea_house, apples).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for oid in OBJECTS:
        lines.append(asp.fact("gift", oid))
    for pid, place in PLACES.items():
        for oid in OBJECTS:
            if oid in {o for o in OBJECTS}:
                if is_valid_combo(pid, oid):
                    lines.append(asp.fact("afford", pid, oid))
    lines.append(asp.fact("blocked", "tea_house", "lantern"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming China story world with an inner monologue and a surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["grandmother", "grandfather"])
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
    valid = valid_combos()
    filtered = [
        (p, o) for p, o in valid
        if (args.place is None or p == args.place)
        and (args.object is None or o == args.object)
    ]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")

    place, obj = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    caregiver = args.caregiver or rng.choice(["grandmother", "grandfather"])
    hero_type = "girl" if gender == "girl" else "boy"
    return StoryParams(
        place=place,
        object=obj,
        hero_name=name,
        hero_type=hero_type,
        caregiver_type=caregiver,
    )


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
        print("\n--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for p, o in combos:
            print(p, o)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [
            generate(StoryParams(place=p, object=o, hero_name="Mei", hero_type="girl", caregiver_type="grandmother"))
            for p, o in valid_combos()
        ]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
